import unittest
import bmt_parser.collaborators as collabs
import pandas as pd


class Test_collabs(unittest.TestCase):

    def test_repeat_collab(self):
        testdata = {
            'issue_id': [1, 1, 1, 2, 2],
            'authors': ['a', 'b', 'c', 'a', 'b']
        }
        testdata = pd.DataFrame(testdata)
        result = collabs.get_collaborators(testdata)
        as_list = []
        for i, row in result.iterrows():
            as_list.append(row.tolist())

        self.assertEqual(len(as_list), 3)
        self.assertTrue(['a', 'b', 2] in as_list)
        self.assertTrue(['a', 'c', 1] in as_list)
        self.assertTrue(['b', 'c', 1] in as_list)

    def test_multiple_authors(self):
        testdata = {
            'issue_id': [1, 2],
            'authors': ['a||b||c', 'a||b']
        }
        testdata = pd.DataFrame(testdata)

        result = collabs.get_collaborators(testdata)

        as_list = []
        for i, row in result.iterrows():
            as_list.append(row.tolist())

        self.assertEqual(len(as_list), 3)
        self.assertTrue(['a', 'b', 2] in as_list)
        self.assertTrue(['a', 'c', 1] in as_list)
        self.assertTrue(['b', 'c', 1] in as_list)
