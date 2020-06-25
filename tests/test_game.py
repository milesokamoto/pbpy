import unittest
import modules.game as game

class TestGame(unittest.TestCase):
    def setUp(self):
        self.id = 4586702
        self.testgame = game.Game(self.id)
    
    # def tearDown(self):
    #     #use if we need to delete files that we created for instance

    def test_get_pbp(self):
        self.assertFalse(len(game.get_pbp(self.id)) > 30)

    def test_create_game(self):
        #TODO: Tests for creating game
        self.assertTrue(True)

    def test_check_subs(self):
        self.testgame.check_subs()

    def test_check_lineups(self):
        self.assertTrue(self.testgame.check_lineups())


    def test_create_plays(self):
        self.testgame.check_subs()
        self.testgame.create_plays()
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()