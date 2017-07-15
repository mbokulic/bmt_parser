'''
Functions for parsing the alto files that contain OCRed text for an issue.
Use the main() function.
'''

import bs4
import re
import os
import logging
from bmt_parser.MyError import MyError


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)

file_handler = logging.FileHandler('parse.log')
file_handler.setLevel(logging.WARNING)
logger.addHandler(file_handler)


def main(mets, alto_dir):
    '''
    @param mets: dictionary that is the result of the parse_mets module
    '''
    # organize the mets subsections by file
    tf = _by_file(mets)

    # get the text for each subsection
    for alto_file in tf:
        root = _get_alto_xml(alto_file, alto_dir)

        # getting the text for each section and subsection
        for subsection in tf[alto_file]:
            text = _get_text_from_alto(root, subsection['loc'])
            subsection['text'] = text

    # flatten the file
    flat = []
    for file in tf:
        flat.extend(tf[file])
    # order alto file by location
    flat = sorted(flat, key=lambda e: e['loc'])

    # organize by section id
    by_section = {}
    for subsection in flat:
        s_id = subsection['section_id']
        if s_id not in by_section:
            by_section[s_id] = {}

        name = subsection['subsection']
        if subsection['subsection'] not in by_section[s_id]:
            by_section[s_id][name] = subsection['text']
        else:
            by_section[s_id][name] = ' '.join([by_section[s_id][name],
                                               subsection['text']])

    return by_section


def _flatten_section(elem):
    result = []

    names = elem['subsections'].keys()
    for name in names:
        subsection = elem['subsections'][name]
        if subsection:
            for loc in subsection:
                data = {}
                data['subsection'] = name
                data['section_id'] = elem['section_id']
                data['file'] = loc['file']
                data['loc'] = loc['loc']
                result.append(data)
    return result


def _by_file(mets):
    mets = [item for sublist in mets['sections']
            for item in _flatten_section(sublist)]

    by_file = {}
    for subsect in mets:
        file = subsect['file']
        if file not in by_file:
            by_file[file] = []
        del subsect['file']
        by_file[file].append(subsect)

    return by_file


def _get_alto_xml(name, path):
    numbers = re.search('[0-9]+', name)
    numbers = name[numbers.start():numbers.end()]
    numbers = numbers[1:]

    files = os.listdir(path)

    r = re.compile(numbers)
    found = list(filter(r.search, files))
    if len(found) is 0:
        raise MyError('file for {} not found'.format(name))
    elif len(found) > 1:
        raise MyError('multiple files for {} found'.format(name))
    else:
        filepath = os.path.join(path, found[0])
        return bs4.BeautifulSoup(open(filepath, 'r'), 'xml')


def _get_text_from_alto(alto_xml, location):
    block = alto_xml.find_all('TextBlock', ID=location)
    if len(block) > 1:
        raise MyError('more than one TextBlock for {}'.format(location))
    elif len(block) == 0:
        raise MyError('no TextBlock for {}'.format(location))

    strings = block[0].find_all('String')
    remove = []

    for idx in range(len(strings)):
        s = strings[idx]
        hyphen = s.get('SUBS_TYPE')
        if hyphen:
            if hyphen == 'HypPart1':
                s['CONTENT'] = s['SUBS_CONTENT']
            elif hyphen == 'HypPart2':
                remove.append(idx)
            else:
                raise MyError('more than two hyphen parts? String: {}'
                              .format(s['CONTENT']))
    strings = [i['CONTENT'].replace('\t', ' ' * 4)
               for j, i in enumerate(strings) if j not in remove]
    return ' '.join(strings)
