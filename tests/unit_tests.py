import unittest
import bmt_parser.collaborators as collabs
import bmt_parser.name_corrections as corr
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


class Test_corrections(unittest.TestCase):

    def test_are_initials(self):
        self.assertTrue(corr.are_initials('M.B.'))
        self.assertTrue(corr.are_initials('M. B.'))
        self.assertTrue(corr.are_initials('M.  B.'))
        self.assertTrue(corr.are_initials('M. v. B.'))
        self.assertTrue(corr.are_initials('A. C. W.'))
        self.assertTrue(corr.are_initials('M B.'))
        self.assertTrue(corr.are_initials('A. L'))
        self.assertTrue(corr.are_initials('M   B'))
        self.assertTrue(corr.are_initials('Dr. M. B.'))

    def test_arent_initials(self):
        self.assertFalse(corr.are_initials('M.Bokulic'))
        self.assertFalse(corr.are_initials('Dr. W. Pape'))
        self.assertFalse(corr.are_initials('Schwitters'))
        self.assertFalse(corr.are_initials('W.Decksel'))
        self.assertFalse(corr.are_initials('T'))
        self.assertFalse(corr.are_initials('T.'))
        self.assertFalse(corr.are_initials('P.L. Flouquet'))
        self.assertFalse(corr.are_initials('P. L. Flouquet'))
        self.assertFalse(corr.are_initials('Joseph Aug. Lux'))
        self.assertFalse(corr.are_initials('J. Leonard Roeselare'))

    def test_fix_initials(self):
        self.assertEqual(corr.fix_initials('A. C. W'), 'A. C. W.')
        self.assertEqual(corr.fix_initials('A. D'), 'A. D.')
        self.assertEqual(corr.fix_initials('A. v. K'), 'A. v. K.')
        self.assertEqual(corr.fix_initials('F.H.'), 'F. H.')
        self.assertEqual(corr.fix_initials('R R'), 'R. R.')
        self.assertEqual(corr.fix_initials('R.B.'), 'R. B.')
        self.assertEqual(corr.fix_initials('W. W.'), 'W. W.')
        self.assertEqual(corr.fix_initials('H W'), 'H. W.')
        self.assertEqual(corr.fix_initials('H P.'), 'H. P.')
        self.assertEqual(corr.fix_initials('H    P.'), 'H. P.')
        self.assertEqual(corr.fix_initials('H    P    '), 'H. P.')
        self.assertEqual(corr.fix_initials('H.    P.    '), 'H. P.')

    def test_get_title(self):
        self.assertEqual(corr.get_title_and_rest('Prof. Kochalka')[0],
                         'Prof.')
        self.assertEqual(corr.get_title_and_rest('prof. Kochalka')[0],
                         'Prof.')
        self.assertEqual(corr.get_title_and_rest('Dr. med. A. Meier-Naef')[0],
                         'Dr. med.')
        # subtitle needs to have a dot
        self.assertEqual(corr.get_title_and_rest('Dr med A. Meier-Naef')[0],
                         'Dr.')
        self.assertEqual(corr.get_title_and_rest('Dr. Med. A. Meier-Naef')[0],
                         'Dr.')
        self.assertEqual(corr.get_title_and_rest('Dr. S. Friedlaender')[0],
                         'Dr.')
        self.assertEqual(corr.get_title_and_rest('Dr. phil. G. Räusch')[0],
                         'Dr. phil.')
        self.assertEqual(corr.get_title_and_rest('Prof. Avgust Černigoj')[0],
                         'Prof.')

        # longforms
        self.assertEqual(corr.get_title_and_rest('Doktor phil. G. Räusch')[0],
                         'Dr. phil.')
        self.assertEqual(corr.get_title_and_rest(
                         'Profesor Avgust Černigoj')[0],
                         'Prof.')

        # without titles
        self.assertEqual(corr.get_title_and_rest('Avgust Černigoj')[0],
                         '')

        # testing rest
        self.assertEqual(corr.get_title_and_rest('Prof. Avgust Černigoj')[1],
                         'Avgust Černigoj')
        self.assertEqual(corr.get_title_and_rest('Dr. med. A. Meier-Naef')[1],
                         'A. Meier-Naef')
        self.assertEqual(corr.get_title_and_rest('  A. Meier-Naef')[1],
                         '  A. Meier-Naef')

    def test_strip_year(self):
        self.assertEqual(corr.strip_year("A R. Schönlank"),
                         "A R. Schönlank")
        self.assertEqual(corr.strip_year("Adrian-Nilsson, Gösta, 1884-1965"),
                         "Adrian-Nilsson, Gösta")
        self.assertEqual(corr.strip_year("Albrecht, Emil Oskar 1895-1953"),
                         "Albrecht, Emil Oskar")
        self.assertEqual(corr.strip_year("Alcaro, Rodolfo, 1896-1982"),
                         "Alcaro, Rodolfo")
        self.assertEqual(corr.strip_year("Allwohn, Adolf, 1893-"),
                         "Allwohn, Adolf")
        self.assertEqual(corr.strip_year("Apollinaire, Guillaume, 1880-1918"),
                         "Apollinaire, Guillaume")
        self.assertEqual(corr.strip_year("Baum, Peter, 1939-..."),
                         "Baum, Peter")
        self.assertEqual(corr.strip_year("Berlewi, H. (Henryk), 1894-1967"),
                         "Berlewi, H. (Henryk)")
        self.assertEqual(corr.strip_year("Buzzi, Paolo, -1956"),
                         "Buzzi, Paolo")
        self.assertEqual(corr.strip_year("Byk, Edgar 1883-"),
                         "Byk, Edgar")
        self.assertEqual(corr.strip_year("Jaeger-Mewe, Harrn (1876- )."),
                         "Jaeger-Mewe, Harrn")
        self.assertEqual(corr.strip_year("Leonardo, da Vinci, 1452-1519."),
                         "Leonardo, da Vinci")
        self.assertEqual(corr.strip_year("Topp, Arnold, 1887-1945?"),
                         "Topp, Arnold")
        self.assertEqual(corr.strip_year("Zerbst, Max, 18..-19.."),
                         "Zerbst, Max")

    def test_get_initials(self):
        self.assertEqual(corr.get_initials("Reinhard Goering"), 'R. G.')
        self.assertEqual(corr.get_initials("Herwarth Walden"), 'H. W.')
        self.assertEqual(corr.get_initials("Mary Schneider-Braillard"),
                         'M. S. B.')
        self.assertEqual(corr.get_initials("Franz W. Seiwert"), 'F. W. S.')
        self.assertEqual(corr.get_initials("Aage von Kohl"), 'A. v. K.')
        self.assertEqual(corr.get_initials("A. M. Frey"), 'A. M. F.')
        self.assertEqual(corr.get_initials("Campendonk"), 'C.')
        self.assertEqual(corr.get_initials("L. Wachlmeier"), 'L. W.')
        self.assertEqual(corr.get_initials("Schmidt-Rottluff"), 'S. R.')
        self.assertEqual(corr.get_initials("r delaunay"), 'r. d.')
        self.assertEqual(corr.get_initials("Chr. Berberoff"), 'C. B.')
        self.assertEqual(corr.get_initials("Edm. Kesting"), 'E. K.')
        self.assertEqual(corr.get_initials("LOUIS MARCOUSSIS"), 'L. M.')
        # dont know what to do with this, it doesnt matter
        self.assertEqual(corr.get_initials("365-er Dichter"), '3. e. D.')
        self.assertEqual(corr.get_initials("L'Oeil de Zinc"), 'L. d. Z.')
        self.assertEqual(corr.get_initials("Karl Höfler"), 'K. H.')
        self.assertEqual(corr.get_initials("Ernst Kállai"), 'E. K.')

    def test_order_names(self):
        self.assertEqual(corr.order_names("A R. Schönlank"),
                         "A R. Schönlank")
        self.assertEqual(corr.order_names("Adrian-Nilsson, Gösta"),
                         "Gösta Adrian-Nilsson")
        self.assertEqual(corr.order_names("Albrecht, Emil Oskar"),
                         "Emil Oskar Albrecht")
        self.assertEqual(corr.order_names("Alcaro, Rodolfo"),
                         "Rodolfo Alcaro")
        self.assertEqual(corr.order_names("Berlewi, H. (Henryk)"),
                         "H. (Henryk) Berlewi")
        self.assertEqual(corr.order_names("Jaeger-Mewe, Harrn"),
                         "Harrn Jaeger-Mewe")
        self.assertEqual(corr.order_names("Heemskerck van Beest, Jacoba van"),
                         "Jacoba van Heemskerck van Beest")

    def test_capitalize(self):
        self.assertEqual(corr.capitalize("VERA IDELSON"), "Vera Idelson")
        self.assertEqual(corr.capitalize("VERA IDEL-SON"), "Vera Idel-Son")
        self.assertEqual(corr.capitalize("H. (Henryk) Berlewi"),
                         'H. (Henryk) Berlewi')
        self.assertEqual(corr.capitalize("Borken die Käfer"),
                         'Borken die Käfer')
        self.assertEqual(corr.capitalize("Lajos D'Ebneth"), "Lajos D'Ebneth")
        self.assertEqual(corr.capitalize("Paul NOUGE"), 'Paul Nouge')
        self.assertEqual(corr.capitalize("R. R."), 'R. R.')
        self.assertEqual(corr.capitalize("R. Reiche"), "R. Reiche")
        # this one is very unusual
        self.assertEqual(corr.capitalize("C. O. —E"), "C. O. —e")
