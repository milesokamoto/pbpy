import unittest
import modules.game as game

class TestGame(unittest.TestCase):
    def setUp(self):
        self.ids = [4586702]
    
    # def tearDown(self):
    #     #use if we need to delete files that we created for instance

    def test_get_pbp(self):
        self.assertFalse(len(game.get_pbp(self.ids[0])) > 30)

if __name__ == '__main__':
    unittest.main()