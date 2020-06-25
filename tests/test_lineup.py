import unittest
import modules.lineup as lineup

class TestLineup(unittest.TestCase):
    def setUp(self):
        self.id = 4586702
    
    # def tearDown(self):
    #     #use if we need to delete files that we created for instance

    def test_get_lineups(self):
        testlineup = lineup.Lineups(self.id)
        testlineup.get_lineups()
        self.assertFalse(len(testlineup.a_lineup) is None)

    def test_get_subs(self):
        testlineup = lineup.Lineups(self.id)
        testlineup.get_lineups()
        for player in testlineup.a_subs:
            print(player.__dict__)
        for player in testlineup.h_subs:
            print(player.__dict__)
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()