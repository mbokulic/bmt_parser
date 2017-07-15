'''
This is the top-level script for

 - parsing the xml using mets and alto files
 - disambiguating names from the parsed data
 - transforming the data into a suitable format for drawing graphs

Uses logging, logs to "parse.log" in root. It will empty the log at start.
'''

import logging
import argparse
import os
import pandas as pd
import bmt_parser.config as cf
import bmt_parser.parse_xml as parse_xml
import bmt_parser.disambiguate_names as disambiguate
import bmt_parser.collaborators as for_graph

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)

open('parse.log', 'w').close()  # emptying log
file_handler = logging.FileHandler('parse.log')
file_handler.setLevel(logging.WARNING)
logger.addHandler(file_handler)


parser = argparse.ArgumentParser(
    description='A script for parsing Blue Mountain periodicals data '
    'https://github.com/pulibrary/BlueMountain. You first need to download '
    'the data using the provided bash script. Outputs will be stored in paths '
    'as provided in config.py')

parser.add_argument('--periodical_name', '-name', required=False, help='name '
                    'of the periodical you wish to parse. Will be used for '
                    'naming output')

parser.add_argument('--xml_data_path', '-xml', required=False, help='dir '
                    'where the Blue Mountain data is located. If not provided,'
                    ' no parsing will be done (a lengthy process, you probably'
                    ' want to skip this after the first time)')

parser.add_argument('--disambiguation_file', '-d', required=False,
                    help='path to csv with disambiguations, needs to be tab '
                    'delimited (Blue Mountain provides an Excel file so you '
                    'will need to convert. If not provided, no disambiguation '
                    'will be done.')

parser.add_argument('--tf_for_graph', '-graph', required=False, default=False,
                    action='store_true', help='Flag whether to transform data '
                    'for displaying it as a graph. Will try to find data in '
                    'paths as defined in config.py.')

args = parser.parse_args()

# creating output dir if it does not exist
if not os.path.exists(cf.OUTPUT_DIR):
    os.makedirs(cf.OUTPUT_DIR)

# putting periodical name in output paths
if args.periodical_name:
    paths = {
        key: os.path.join(cf.OUTPUT_DIR,
                          '_'.join([args.periodical_name, cf.PATHS[key]]))
        for key in cf.PATHS.keys()}
else:
    paths = {
        key: os.path.join(cf.OUTPUT_DIR, cf.PATHS[key])
        for key in cf.PATHS.keys()}

# running parser and data transformation code
if args.xml_data_path:
    parse_xml.main(args.xml_data_path, paths['data'])

if args.disambiguation_file:
    data = disambiguate.main(args.disambiguation_file, paths['data'])
    data.to_csv(paths['disamb'], sep=cf.CSV_SEP, index=False)

if args.tf_for_graph:
    if not args.disambiguation_file:
        if os.path.exists(paths['disamb']):
            data = pd.read_csv(paths['disamb'], sep=cf.CSV_SEP)
        elif os.path.exists(paths['data']):
            data = pd.read_csv(paths['data'], sep=cf.CSV_SEP)
        else:
            raise ValueError('no data file for this periodical!')

    collabs = for_graph.get_collaborators(data)
    collabs.to_csv(paths['collabs'], sep=cf.CSV_SEP, index=False)
