import unittest
import modules.names as names
import modules.game as game

class TestNames(unittest.TestCase):
    def setUp(self):
        self.id = 4586702
        self.testgame = game.Game(self.id)
    
    # def tearDown(self):
    #     #use if we need to delete files that we created for instance

    def test_get_names(self):
        test_names = names.NameDict(self.testgame)
        print(test_names.__dict__)
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()