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

import logging
import pandas as pd
import numpy as np
import re
import bmt_parser.config as cf


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)

file_handler = logging.FileHandler('parse.log')
file_handler.setLevel(logging.WARNING)
logger.addHandler(file_handler)


def prepare_disambiguation_file(path):
    table = pd.read_csv(path, sep=cf.CSV_SEP)
    table = table.loc[:, ['Unique Names', 'NameCopy']]
    table.rename(columns={'Unique Names': 'found_name',
                          'NameCopy': 'official_name'},
                 inplace=True)

    # searching for cases when official name is repeated as found name
    copy = table.loc[table['official_name'] != table['found_name'], :]
    names = list(copy['found_name'])
    cases = [_ for _ in copy['official_name'] if _ in names]

    # replacing those names
    replacements = {'official_name': {}}
    for official_name in cases:
        idx_found = table['found_name'] == official_name
        # should have only one True
        if sum(idx_found) != 1:
            raise ValueError('duplicated found names!')
        idx_found = np.nonzero(idx_found)[0][0]
        new_name = table.get_value(index=idx_found, col='official_name')
        replacements['official_name'][official_name] = new_name

    table = table.replace(to_replace=replacements)

    # removing years from the name
    # and turning into dict
    result = {}
    regex = '\(?(, | )?[0-9]+-?[0-9]*\)?'
    for i, row in table.iterrows():
        name = row['official_name']
        if name is not np.nan:
            new_name = re.sub(regex, '', name)
            table.set_value(i, 'official_name', new_name)
        result[row['found_name']] = row['official_name']

    return result


def disambiguate_names(original_data, disamb_data):
    for i, row in original_data.iterrows():
        if row.authors is not np.nan:
            multiple = re.search('||', row.authors)
            try:
                if multiple:
                    authors = row.authors.split('||')
                    authors = [disamb_data[author] for author in authors]
                    original_data.set_value(i, 'authors', '||'.join(authors))
                else:
                    original_data.set_value(i, 'authors',
                                            disamb_data[row.authors])
            except KeyError:
                logger.warning('author(s) {} do not have disambiguations'
                               .format(row.authors))

    return original_data


def main(disamb_path, original_path):
    disamb_data = prepare_disambiguation_file(disamb_path)
    original_data = pd.read_csv(original_path, delimiter=cf.CSV_SEP)
    new_file = disambiguate_names(original_data, disamb_data)
    return new_file


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--disambiguation_path', '-d', required=True,
                        help='path to csv with disambiguations.')
    parser.add_argument('--data_file', '-f', required=True,
                        help='path to csv with data on authors and texts.')
    args = parser.parse_args()

    open('parse.log', 'w').close()  # emptying log
    main(args.disambiguation_path, args.data_file)
