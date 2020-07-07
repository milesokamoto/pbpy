import unittest
import modules.scrape as scrape

class TestScrape(unittest.TestCase):
    def setUp(self):
        self.id = 4586702
    
    # def tearDown(self):
    #     #use if we need to delete files that we created for instance

    def test_get_lu_table(self):
        self.assertFalse(scrape.get_lu_table(self.id) is None)

if __name__ == '__main__':
    unittest.main()