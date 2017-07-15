'''
transforms the csv output that was parsed from Blue Mountain
'''

import pandas as pd
import numpy as np
import itertools


def get_collaborators(data):
    '''
    takes a pandas DataFrame that is the output of 01_parse_xml.py and
    transforms it into a df that counts the number of collaborations btw two
    authors
    '''
    # need only the sections where an author is present
    has_author = [author is not np.nan for author in data.authors]
    data = data.loc[has_author, ['issue_id', 'authors']]

    # creating a list of collaborator pairs for each issue
    issues = set(data.issue_id)
    collaborators = []
    for issue in issues:
        target = _unique_collaborators(data.authors[data.issue_id == issue])
        collaborators.extend(target)

    # counting the nr of collaborations
    numbered = {}
    for collab in collaborators:
        try:
            numbered[collab] += 1
        except KeyError:
            numbered[collab] = 1

    # data transform: parsing the string and turning into a pd dataframe
    records = []
    for key in numbered.keys():
        collabs = key.split('||')
        records.append([collabs[0], collabs[1], numbered[key]])
    result = pd.DataFrame.from_records(
        records, columns=['author1', 'author2', 'count'])

    return result


def _unique_collaborators(authors):
    '''
    returns a list of strings like "author1||author2"
    '''
    # first I need to separate multiple authors
    separated = []
    for string in authors:
        target = string.split('||')
        separated.extend(target)
    # then create a Cartesian product of the authors and remove duplicates
    # and authorA-authorA combinations
    product = list(itertools.product(separated, repeat=2))
    product = ['||'.join(sorted(collabs)) for collabs in product
               if collabs[0] != collabs[1]]
    product = list(set(product))
    return product


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--path', '-p', required=False,
                        help='path to csv file. If None, will try output.csv')
    args = parser.parse_args()
    path = args.path if args.path else 'output.csv'

    data = pd.read_csv(path, delimiter='\t')

    result = get_collaborators(data)
