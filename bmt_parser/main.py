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


parser = argparse.ArgumentParser()
parser.add_argument('--periodical_name', '-name', required=False)
parser.add_argument('--xml_data_path', '-xml', required=False)
parser.add_argument('--disambiguation_file', '-d', required=False,
                    help='path to csv with disambiguations.')
parser.add_argument('--tf_for_graph', '-graph', required=False, default=False,
                    action='store_true')
args = parser.parse_args()

if args.periodical_name:
    paths = {
        key: os.path.join(cf.OUTPUT_DIR,
                          '_'.join([args.periodical_name, cf.PATHS[key]]))
        for key in cf.PATHS.keys()}
else:
    paths = {
        key: os.path.join(cf.OUTPUT_DIR, cf.PATHS[key])
        for key in cf.PATHS.keys()}

if args.xml_data_path:
    parse_xml.main(args.xml_data_path, paths['data'])

if args.disambiguation_file:
    data = disambiguate.main(args.disambiguation_file, paths['data'])
    data.to_csv(paths['disamb'], sep=cf.CSV_SEP, index=False)

if args.tf_for_graph:
    collabs = for_graph.get_collaborators(data)
    collabs.to_csv(paths['collabs'], sep=cf.CSV_SEP, index=False)
