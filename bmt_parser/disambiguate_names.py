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


TO DO

  3) kratica bez razmaka ista je kratici s razmakom (D. O = D.O.)
  4) ako postoji kratica (X.Y. i na korpusu postoji samo jedna osoba s tim
     inicijalima, onda je to ta osoba)

  2) ako ima zarez, onda razreži i stavi ime na početak i prezime na kraj
  1) stripp-aj sve interpunkcije na kraju niza (npr. Zerbst, Max..-.. ili
     Jaeger-Mewe, Harrn  ).)
  3) ručno prođi i malo poglečni zdravoseljački:

Prof. Avgust Černigoj
Prof. Avgust Cernigoj

r delaunay
Robert Delauany

Moritz König
Moriz König

Edm. Kesting
EDMUND KESTING
Kesting, Edmund

Edmund Palasovsky
Edmund Palasowsky

Josef Treß
Josef Tress
Joseph Tress

Jacoba Van Heemskerck
Jacoba van Heemskreck
'''

import logging
import pandas as pd
import numpy as np
import re
import bmt_parser.config as cf
import bmt_parser.name_corrections as corr

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler('parse.log')
file_handler.setLevel(logging.WARNING)
logger.addHandler(file_handler)


def prepare_disambiguation_file(path, names_in_data):
    '''
    path: path to disamb file
    names_in_data: Set of unique names present in the dataset
    '''
    table = pd.read_csv(path, sep=cf.CSV_SEP)
    table = table.loc[:, ['Unique Names', 'NameCopy']]
    table.rename(columns={'Unique Names': 'found',
                          'NameCopy': 'resolved'},
                 inplace=True)

    table = add_missing_names(table, names_in_data)
    table = correct_names(table)
    # result = fix_repeated_resolved(table)
    return table


def add_missing_names(table, names_in_data):
    names_in_disamb = set(table.found)
    # names in disamb but not in data.
    # these might indicate an error in parsing
    not_found = names_in_disamb.difference(names_in_data)
    percent_format = "{:.1%}".format(len(not_found) / len(names_in_disamb))
    logger.warning('{} names in disambiguation ({}) not present in the dataset'
                   .format(len(not_found), percent_format))
    logger.warning('\n'.join(sorted(not_found)))
    logger.warning('\n')

    # reverse: names that are present in the dataset but not in the disamb file
    not_found = names_in_data.difference(names_in_disamb)
    percent_format = "{:.1%}".format(len(not_found) / len(names_in_data))
    logger.warning('{} names ({}) not found in the disambiguation file'
                   .format(len(not_found), percent_format))
    logger.warning('\n'.join(sorted(not_found)))
    logger.warning('\n')

    # adding missing names to table
    missing_names = pd.DataFrame([[name, name] for name in not_found],
                                 columns=['found', 'resolved'])
    table = table.append(missing_names, ignore_index=True)

    return table


def correct_names(table):
    titles = [corr.get_title_and_rest(name) for name in table['found']]
    names = [t[1] for t in titles]
    titles = [t[0] for t in titles]

    table['titles'] = pd.Series(titles)

    initials = [corr.fix_initials(name) if corr.are_initials(name)
                else corr.get_initials(name) for name in names]
    table['initials'] = pd.Series(initials)

    table['found_are_initials'] = pd.Series([corr.are_initials(name)
                                            for name in names])

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

    table = table.replace(to_replace=replacements)

    # removing years from the name
    # and turning into dict
    result = {}
    regex = '\(?(, | )?[0-9]+-?[0-9]*\)?'
    for i, row in table.iterrows():
        name = row['resolved']
        if name is not np.nan:
            new_name = re.sub(regex, '', name)
            table.set_value(i, 'resolved', new_name)
        result[row['found']] = row['resolved']

    return result


def disambiguate_names(original_data, disamb_data):
    for i, row in original_data.iterrows():
        if row.authors is not np.nan:
            multiple = re.search(cf.AUTHOR_SEP, row.authors)
            try:
                if multiple:
                    authors = row.authors.split(cf.AUTHOR_SEP)
                    authors = [disamb_data[author] for author in authors]
                    original_data.set_value(i, 'authors', cf.AUTHOR_SEP.join(authors))
                else:
                    original_data.set_value(i, 'authors',
                                            disamb_data[row.authors])
            except KeyError:
                logger.warning('author(s) "{}" do not have disambiguations'
                               .format(row.authors))

    return original_data


def main(disamb_path, original_path):
    original_data = pd.read_csv(original_path, delimiter=cf.CSV_SEP)

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

    disamb_data = prepare_disambiguation_file(disamb_path, unique_names)
    return disamb_data
    # new_file = disambiguate_names(original_data, disamb_data)
    # return new_file


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--disambiguation_path', '-d', required=True,
                        help='path to csv with disambiguations.')
    parser.add_argument('--data_file', '-f', required=True,
                        help='path to csv with data on authors and texts.')
    args = parser.parse_args()

    open('parse.log', 'w').close()  # emptying log
    res = main(args.disambiguation_path, args.data_file)
    res.to_csv('./output/test.csv', index=False)
