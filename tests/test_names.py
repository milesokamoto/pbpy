import unittest
import modules.names as names
import modules.lineup as lineup
import modules.game as game

class TestNames(unittest.TestCase):
    def setUp(self):
        self.id = 4926879
        # self.testgame = game.Game(self.id)
    
    # def tearDown(self):
    #     #use if we need to delete files that we created for instance

    def test_match_all(self):
        lu = lineup.Lineup(self.id, 0)
        pl = game.get_pbp(self.id)
        lu = names.match_all(lu, pl)
        self.assertTrue(len([p.pbp_name for p in lu.lineup if p.pbp_name == '']) == 0 and len([p.pbp_name for p in lu.subs if p.pbp_name == '']) == 0)

if __name__ == '__main__':
    unittest.main()