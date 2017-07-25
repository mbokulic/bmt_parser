#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
functions that disambiguate names using an external file.

Inputs are:

  - a tab delimited csv with columns "Unique Names" (= found name, as in the
  text) and "NameCopy" (the right name)
  - output from 01_parse_xml.py

The "disambiguate_names" function will use the disambiguation file to change
the names in the output from parse_xml.

If you want to save the log file, then rename the 'parse.log' file since it is
overwritten every time
'''

import json
import logging
import pandas as pd
import numpy as np
import re
import bmt_parser.config as cf
import bmt_parser.name_corrections as corr

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler('parse.log')
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)


def prepare_disambiguation_file(path, names_in_data, name_replacements=None):
    '''
    path: path to disamb file
    names_in_data: Set of unique names present in the dataset
    name_replacements: dict where key=resolved name, and value=replacement
    '''
    table = pd.read_csv(path, sep=cf.CSV_SEP)
    table = table.loc[:, ['Unique Names', 'NameCopy']]
    table.rename(columns={'Unique Names': 'found',
                          'NameCopy': 'resolved'},
                 inplace=True)

    # removing NaN values in found
    table = table.loc[table['found'].notnull(), :]
    # when no resolved name, replace with found
    idx = table['resolved'].isnull()
    empty_names = table.loc[idx, 'found']
    table.loc[idx, 'resolved'] = empty_names

    # corrections
    table = add_missing_names(table, names_in_data)

    if name_replacements:
        counter = 0
        for key, value in name_replacements.items():
            table['resolved'][table['resolved'] == key] = value
            counter += 1
        logger.warning('{} names were replaced with values in '
                       'the provided name_replacement json'.format(counter))

    table = fix_names(table)
    table = fix_repeated_resolved(table)
    table = resolve_initials(table)

    return table


def add_missing_names(table, names_in_data):
    '''adds names that are in the dataset but not in the disambiguation file
    '''
    names_in_disamb = set(table.found)
    # names in disamb but not in data.
    # these might indicate an error in parsing
    not_found = names_in_disamb.difference(names_in_data)
    percent_format = "{:.1%}".format(len(not_found) / len(names_in_disamb))
    logger.warning('{} names in disambiguation ({}) not present in the dataset'
                   .format(len(not_found), percent_format))
    logger.info('\n'.join(sorted(not_found)))

    # reverse: names that are present in the dataset but not in the disamb file
    not_found = names_in_data.difference(names_in_disamb)
    percent_format = "{:.1%}".format(len(not_found) / len(names_in_data))
    logger.warning('{} names ({}) not found in the disambiguation file'
                   .format(len(not_found), percent_format))
    logger.info('\n'.join(sorted(not_found)))

    # adding missing names to table
    missing_names = pd.DataFrame([[name, name] for name in not_found],
                                 columns=['found', 'resolved'])
    table = table.append(missing_names, ignore_index=True)

    return table


def fix_names(table):
    # stripping whitespace
    table['resolved'] = pd.Series([s.strip() for s in table['resolved']])
    table['found'] = pd.Series([s.strip() for s in table['found']])

    # removing strange characters (string terminators, etc)
    table['resolved'] = table['resolved'].apply(corr.remove_strange_chars)
    table['found'] = table['found'].apply(corr.remove_strange_chars)

    # removing years from resolved names
    table['resolved_original'] = table['resolved']
    table['resolved'] = table['resolved'].apply(corr.strip_year)

    # transforming into "Name Surname" for resolved names
    table['resolved'] = table['resolved'].apply(corr.order_names)

    # getting title (Dr., Prof.) and storing into the table
    titles = [corr.get_title_and_rest(name) for name in table['found']]
    names = [t[1] for t in titles]
    titles = [t[0] for t in titles]
    table['titles'] = pd.Series(titles)

    # turning all caps into proper form
    table['resolved'] = table['resolved'].apply(corr.capitalize)
    table['found'] = table['found'].apply(corr.capitalize)

    # getting initials from name
    initials = [corr.fix_initials(name) if corr.are_initials(name)
                else corr.get_initials(name) for name in names]
    table['initials_found'] = pd.Series(initials)
    table['initials_resolved'] = table['resolved'].apply(corr.get_initials)

    table['found_are_initials'] = pd.Series([corr.are_initials(name)
                                            for name in names])

    # getting the surname
    splits = [name.split(' ') for name in table['found']]
    table['surname_found'] = pd.Series([s[len(s) - 1] for s in splits])

    return table


def resolve_initials(table):
    # getting resolved names initials
    tgt = table.loc[~table['found_are_initials'],
                    ['initials_resolved', 'resolved']].itertuples()
    tgt = [(t[1], t[2]) for t in tgt]
    tgt = list(set(tgt))

    counts = {}
    for i in tgt:
        initials = i[0].upper()  # disregarding lowercase letters
        try:
            counts[initials]['count'] += 1
        except KeyError:
            counts[initials] = {}
            counts[initials]['name'] = i[1]
            counts[initials]['count'] = 1
    replacements = {c[0]: c[1]['name'] for c in counts.items()
                    if c[1]['count'] == 1}

    # initials that do not have a full name
    indices = table.loc[table['found_are_initials'], :].index
    for idx in indices:
        row = table.iloc[idx, ]
        try:
            initials = row['initials_found']
            logger.warning('replacements found for "{}": "{}"'.format(
                           initials, replacements[initials]))
        except KeyError:
            logger.warning('no replacement found for initials "{}"'
                           .format(initials))

    return table


def fix_repeated_resolved(table):
    # searching for cases when resolved name is repeated as found name
    copy = table.loc[table['resolved'] != table['found'], :]
    names = list(copy['found'])
    cases = [_ for _ in copy['resolved'] if _ in names]

    # replacing those names
    replacements = {'resolved': {}}
    for resolved in cases:
        idx_found = table['found'] == resolved
        # should have only one True
        if sum(idx_found) != 1:
            raise ValueError('duplicated found names!')
        idx_found = np.nonzero(idx_found)[0][0]
        new_name = table.get_value(index=idx_found, col='resolved')
        replacements['resolved'][resolved] = new_name

    if replacements['resolved']:
        table = table.replace(to_replace=replacements)

    return table


def disambiguate_names(original_data, disamb_data):
    disamb_data = {row[1]: row[2] for row
                   in disamb_data.loc[:, ['found', 'resolved']].itertuples()}
    for i, row in original_data.iterrows():
        if row.authors is not np.nan:
            multiple = re.search(cf.AUTHOR_SEP, row.authors)
            try:
                if multiple:
                    authors = [corr.capitalize(a.strip()) for a
                               in row.authors.split(cf.AUTHOR_SEP)]
                    authors = [disamb_data[author] for author in authors]
                    original_data.set_value(
                        i, 'authors', cf.AUTHOR_SEP.join(authors))
                else:
                    author = corr.capitalize(row.authors.strip())
                    original_data.set_value(i, 'authors',
                                            disamb_data[row.authors])
            except KeyError:
                logger.warning('author(s) "{}" do not have disambiguations'
                               .format(row.authors))

    return original_data


def main(disamb_path, original_path, name_replacements_path,
         disamb_write_path=None):
    original_data = pd.read_csv(original_path, delimiter=cf.CSV_SEP)

    if name_replacements_path:
        name_replacements = json.load(open(name_replacements_path, 'r'))

    # gathering all unique names in the data into a set
    unique_names = []
    for author in original_data['authors']:
        if author is not np.nan:
            if re.search(cf.AUTHOR_SEP, author):
                author_split = author.split('||')
                unique_names.extend(author_split)
            else:
                unique_names.append(author)
    unique_names = set(unique_names)

    disamb_data = prepare_disambiguation_file(disamb_path, unique_names,
                                              name_replacements)
    if disamb_write_path:
        disamb_data.to_csv(disamb_write_path, index=False)

    new_file = disambiguate_names(original_data, disamb_data)
    return new_file


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--disambiguation_path', '-d', required=True,
                        help='path to csv with disambiguations.')
    parser.add_argument('--data_file', '-f', required=True,
                        help='path to csv with data on authors and texts.')
    parser.add_argument('--name_replacements', '-n', required=False,
                        help='path to json with name replacements.')
    parser.add_argument('--store_disamb', '-sd',
                        required=False,
                        help=('path where to store corrected disambiguation'
                              'file'))

    args = parser.parse_args()

    open('parse.log', 'w').close()  # emptying log

    res = main(args.disambiguation_path, args.data_file, name_replacements,
               args.store_disamb)
