'''
Parses the Blue Mountain text data for the Der Sturm magazine, possibly for
others as well if they have the same structure.

You should first download the data using download_from_github.sh.

for each journal get
    - metadata: date, volume, name
    - list of editors
    - list of texts (title, author, text)

columns:

 - issue_id: an incremental ID
 - date: date when issued
 - volume: issue volume
 - number: issue number
 - section_id: section ID is from Blue Mountain documents
 - title: title of the section (a text, image, etc)
 - authors: authors separated with "||"
 - section_type: image, advertisement, or text type (flat, parent, subsection)
 - type_of_resource: still image, text (keeping this if there are any surprises
(and the following are text parts)
 - Head
 - Subhead
 - Byline
 - Copy

'''

import bmt_parser.parse_mets as mets
import bmt_parser.parse_alto as alto
import os
import re
import logging
import csv
import bmt_parser.config as cf

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)

open('parse.log', 'w').close()  # emptying log
file_handler = logging.FileHandler('parse.log')
file_handler.setLevel(logging.WARNING)
logger.addHandler(file_handler)

# overwrite with your directory!
entry_dir = './data/issues'
csv_path = 'output.csv'
columns = ["issue_id", "date", "volume", "number", "section_id", "title",
           "authors", "section_type", "type_of_resource", "Head", "Subhead",
           "Byline", "Copy"]


def get_issue(mets_path, alto_dir, issue_id):
    try:
        mets_data = mets.main(mets_path)
        alto_data = alto.main(mets_data, alto_dir)
    except Exception as e:
        if type(e).__name__ == 'MyError':
            logger.error(str(e))
        else:
            logger.exception(mets_path + ': ' + str(e))
        return None

    # join mets and alto file
    sections = mets_data['sections']
    del mets_data['sections']
    for section in sections:
        section.update(mets_data)
        try:
            target = alto_data[section['section_id']]
            section.update(target)
        except KeyError:
            pass
        for subsect in section['subsections']:
            if section['subsections'][subsect] is None:
                section[subsect] = ''

        section['issue_id'] = issue_id
        del section['subsections']

    return sections


def main(data_dir):
    # writing column names
    csv_file = csv.DictWriter(open(csv_path, 'w'), columns,
                              delimiter=cf.CSV_SEP)
    csv_file.writeheader()

    # getting data out
    issue_id = 1

    for dirpath, dirnames, filenames in os.walk(entry_dir):
        if not dirnames:  # starting at lowest level dir
            # alto files
            if not re.search('alto$', dirpath):
                logger.warning('no alto dir in {}'.format(dirpath))
                continue
            alto_dir = dirpath

            # mets file
            mets_dir = os.path.split(alto_dir)[0]
            mets_file = [file for file in os.listdir(mets_dir)
                         if re.search('mets\.xml$', file)]
            if not mets_file:
                logger.warning('no mets file for {}'.format(mets_dir))
                continue
            else:
                mets_path = os.path.join(mets_dir, mets_file[0])

            # getting data for single issue
            logger.info('started file {}'.format(mets_file))
            result = get_issue(mets_path, alto_dir, issue_id)
            issue_id += 1
            if result:  # get_issue will return None if problems
                csv_file.writerows(result)


if __name__ == '__main__':
    main('../data/issues', '../output/data.csv')
