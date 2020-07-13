import unittest
import modules.game as game
import modules.names as names
import modules.ui as ui
import pandas as pd

class TestGame(unittest.TestCase):
    def setUp(self):
        self.id = 4926019
        # 4926865, 4925736, 4926879, 4586702
        self.testgame = game.Game(self.id)
    
    # def tearDown(self):
    #     #use if we need to delete files that we created for instance

    def test_get_pbp(self):
        self.assertFalse(len(game.get_pbp(self.id)) > 30)

    def test_create_game(self):
        ui.print_lineups(self.testgame)
        ui.print_subs(self.testgame)
        #TODO: Tests for creating game
        self.assertTrue(True)

    def check_order(self):
        self.testgame.play_list = game.get_pbp(self.id)
        self.testgame.check_order()
        self.assertTrue(True)

    def test_check_subs(self):
        self.testgame.play_list = game.get_pbp(self.id)
        for lu in self.testgame.lineups:
            names.match_all(lu, self.testgame.play_list)
        # print([p.__dict__ for p in self.testgame.lineups[0].lineup])
        self.testgame.check_subs()
        self.assertTrue(len([s for s in self.testgame.subs.values() if not 'text' in s]) == 0)

    def test_create_plays(self):
        self.testgame.play_list = game.get_pbp(self.id)
        for lu in self.testgame.lineups:
            names.match_all(lu, self.testgame.play_list)
        self.testgame.check_subs()
        self.testgame.create_plays()
        self.assertTrue(True)

    def test_make_sub(self):
        self.testgame.play_list = game.get_pbp(self.id)
        for lu in self.testgame.lineups:
            names.match_all(lu, self.testgame.play_list)
        self.testgame.check_subs()
        self.testgame.check_subs()
        self.testgame.create_plays()
        for h in self.testgame.events:
            for e in h:
                if "sub" in str(type(e)):
                    self.testgame.lineups[e.team].make_sub(e)
                    # ui.print_lineups(self.testgame)
            self.testgame.state['half'] = (self.testgame.state['half']  + 1) % 2   
            check = game.check_lineup(self.testgame.lineups[(self.testgame.state['half'] + 1) % 2].lineup)
        self.assertTrue(check)

    def test_execute_game(self):
        self.testgame.setup_game()
        output = self.testgame.execute_game()
        print((pd.DataFrame(output).iloc[0:,:15]))
        self.assertTrue(True)
            

if __name__ == '__main__':
    unittest.main()