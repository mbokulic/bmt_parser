'''
Functions for parsing the toplevel mets file that contains metadata on an
issue.
Use the main() function.

TO DO

 - I've seen that <typeOfResource>still image</> can be <genre>Music</genre>
   I don't know if this distinction is important and should I record genre
'''

import bs4
import logging
import os
import re
from bmt_parser.MyError import MyError


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)

file_handler = logging.FileHandler('parse.log')
file_handler.setLevel(logging.WARNING)
logger.addHandler(file_handler)


KNOWN_SUBS = ['Head', 'Subhead', 'Byline', 'Copy', 'TextContent',
              'Illustration',
              'Music',      # not sure what to do with this one
              'MinorHead']  # only one example

RELEVANT_SUBS = ['Head', 'Subhead', 'Byline', 'Copy']
VALID_SECTIONS = ['advertisement', 'parent', 'subsection', 'flat', 'image']


def main(filepath):
    '''returns the mets (metadata) info on an issue:
      - issue date, volume, etc
      - list of sections (texts, images) and their metadata

    :param filepath: path to the mets file
    :returns: a nested dictionary
    '''

    result = {}

    with open(filepath, 'r') as file:
        root = bs4.BeautifulSoup(file, 'xml')

    filename = os.path.split(filepath)[1]

    # getting data
    result.update(_get_issue_metadata(root, filename))
    result['sections'] = _get_issue_sections(root, filename)

    return result


def _get_issue_metadata(root, filename):
    '''returns metadata (title, date...) in form of a dictionary
    '''

    result = {}
    dmdsec = _only_one(root, 'dmdSec', filename)
    part = _only_one(dmdsec, 'part', filename, {'type': 'issue'})

    result['volume'] = part.find('detail', type='volume').number.string
    result['number'] = part.find('detail', type='number').number.string
    result['date'] = dmdsec.originInfo.find('dateIssued', keyDate='yes').string
    return result


def _get_issue_sections(root, filename):
    '''returns section (texts, images) data as a list
    '''
    # dmdSec was already checked
    dmdsec = _only_one(root, 'dmdSec', filename)
    mods = _only_one(dmdsec, 'mods', filename)
    structMap = _only_one(root, 'structMap', filename,
                          {'LABEL': 'Logical Structure'})

    result = []
    sections = mods.find_all('relatedItem')
    for sec in sections:
        type = _get_section_type(sec, filename)
        if type in VALID_SECTIONS:
            data = _parse_section(sec, type, structMap, filename)
            result.append(data)

    return result


def _parse_section(section, type, structMap, filename):
    '''returns data on a single section as a dict
    '''
    result = {}

    # metadata
    result['title'] = ' '.join([
        part.string for part in section.titleInfo.find_all(True)])

    names = section.find_all('name', recursive=False)
    if names:
        names_text = [name.displayForm.string for name in names
                      if name.role.roleTerm.string == 'cre']
        names_text = [name for name in names_text if name is not None]
        result['authors'] = '||'.join(names_text)
    else:
        result['authors'] = None

    result['type_of_resource'] = section.find('typeOfResource').string
    result['section_id'] = section['ID']

    result['subsections'] = {}

    if type == 'image':
        remaining = RELEVANT_SUBS
    else:
        text_cont = 'SponsoredAd' if type == 'advertisement' else 'TextContent'
        alto_locs = structMap.find('div', TYPE=text_cont, DMDID=section['ID'])
        if not alto_locs:
            raise MyError('section {} in file {} doesnt have a div with text '
                          'content'.format(section['ID'], filename))
        divs = alto_locs.find_all('div', recursive=False)

        div_types = set([div['TYPE'] for div in divs])
        unknown = div_types - set(KNOWN_SUBS)
        if len(unknown) > 0:
            msg = ('div of type {} in section {} of file {} not '
                   'known!'.format(unknown, section['ID'], filename))
            # quick fix for their typo
            if 'Byline          ' in unknown:
                for div in divs:
                    if div['TYPE'] == 'Byline          ':
                        div['TYPE'] = 'Byline'
                # if there are unknown divs left, raise error
                if (len(unknown) - 1) > 0:
                    raise MyError(msg)
            else:
                raise MyError(msg)

        divs = [div for div in divs if div['TYPE'] in RELEVANT_SUBS]
        for div in divs:
            if div['TYPE'] in result:
                raise MyError('duplicate alto location for {}!'.
                              format(div['TYPE']))
            result['subsections'][div['TYPE']] = _get_alto_locations(div)

        remaining = set(RELEVANT_SUBS) - set(div_types)

    for r in remaining:
        result['subsections'][r] = None

    return result


def _only_one(root, tag_name, filename, optional_attr={}):
    '''checks if root contains tag and returns it. Raises errors if no tag or
    more than one tag.
    '''
    tags = root.find_all(tag_name, attrs=optional_attr)
    if len(tags) > 1:
        raise MyError('more than one {tag_name} in {filename}'.format(
            tag_name=tag_name, filename=filename))
    elif len(tags) == 0:
        raise MyError('no {tag_name} in {filename}'.format(
            tag_name=tag_name, filename=filename))
    return tags[0]


def _test_section(section):
    '''returns True if the given section is relevant
    '''
    if section.get('type'):
        if section['type'] == 'constituent':
            return True
    # due to input mistakes, some sections do not have type
    elif section.get('ID'):
        if re.search('c[0-9]{3}', section['ID']):
            return True

    return False


def _get_section_type(section, filename):
    '''returns section type and None if it is an invalid section
    '''
    if not _test_section(section):
        logger.warning('ignoring section: {} {}'
                       .format(section.name, section.attrs))
        return None

    resource_type = section.find('typeOfResource').string
    genre = section.find('genre').string.lower()
    title = section.titleInfo.title.string

    if resource_type == 'still image':
        return 'image'
    elif resource_type == 'text':
        # special text section types
        if 'advertisement' in genre:
            return 'advertisement'
        elif 'inhalt' in title.lower():
            return 'contents'
        # valid sections
        elif len(list(section.find_all('relatedItem',
                                       type='constituent'))) > 0:
            return 'parent'
        elif _test_section(section.parent):
            if _test_section(section.parent.parent):
                raise MyError('double nesting in section {}, file {}!'
                              .format(section['ID'], filename))
            return 'subsection'
        else:
            return 'flat'
    else:
        logger.warning('unknown section {} type in file {}. Resource type: {},'
                       'genre: {}'
                       .format(section['ID'], filename, resource_type, genre))
        return 'unknown'


def _get_alto_locations(section):
    '''returns alto locations as a list. These are used when parsing alto file
    '''
    areas = section.find_all('area')
    if len(areas) == 0:
        return None
    return [{'file': area['FILEID'], 'loc': area['BEGIN']} for area in areas]


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', '-p', dest='file_path', required=True)
    args = parser.parse_args()

    res = main(args.file_path)
    print(json.dumps(res))
