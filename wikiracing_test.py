import unittest

from wikiracing import WikiRacer, InvalidPageException


class WikiRacerTest(unittest.TestCase):

    racer = WikiRacer()

    def test_correct_work(self):
        path = self.racer.find_path('Дружба', 'Рим')
        self.assertEqual(path, ['Дружба', 'Якопо Понтормо', 'Рим'])

    def test_invalid_page_titles_get_aborted(self):
        path_one = self.racer.find_path('GIBIBIBI', 'Вітамін K')    # just some gibberish
        path_two = self.racer.find_path('Вітамін K', 'GIBIBIBI')    # checking both start and end positions
        self.assertNotIsInstance(path_one+path_two, list) # the exception is handled so we get a string as an output!

    def test_technical_articles_get_omitted(self):
        with self.assertRaises(InvalidPageException):
            self.racer._validate_page("Війна:Ресурси")

    def test_link_per_page_limit(self):
        """Testing that we only retrieve 200 first links."""
        path = self.racer._get_links('Україна') # this page has way more than 200 links
        self.assertEqual(len(path), 200)        

    def test_backlinks_retrieved(self):
        """Testing that backlinks are actually different from links."""
        backlinks = self.racer._get_backlinks('Україна')    
        links = self.racer._get_links('Україна')
        self.assertNotEqual(backlinks, links)


if __name__ == '__main__':
    unittest.main()
