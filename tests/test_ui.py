import unittest
import modules.lineup as lineup
import modules.ui as ui
import modules.game as game

class TestUi(unittest.TestCase):
    def setUp(self):
        self.id = 4586702
        self.testgame = game.Game(self.id)

    
    # def tearDown(self):
    #     #use if we need to delete files that we created for instance

    def test_lineup_ui(self):
        ui.print_lineups(self.testgame)
        self.assertTrue(True)

    def test_subs_ui(self):
        ui.print_subs(self.testgame)
        self.assertTrue(True)

    def test_state_ui(self):
        ui.print_state(self.testgame)
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()