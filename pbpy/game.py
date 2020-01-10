import scrape
import parse
import pandas as pd
import re
import lineup
import names

class Game:
    def __init__(self, id):
        self.id = id
        # self.meta = get_info(id) #should be separate db table
        self.game = get_pbp(self.id)
        self.play = 0
        self.half = 0 # inning is trunc(div/2)+1, top/bottom is even/odd
        self.lineups = lineup.Lineups(self.id) # 2 lineup objects, 2 sub lists
        self.runners = ['']*3
        self.outs = 0
        self.count = [0, 0] #balls/strikes/outs
        self.h_order = 0
        self.a_order = 0
        self.score = [0,0]
        self.defense = self.get_defense()
        self.leadoff_fl = True
        self.names = names.NameDict(self.lineups)

    def advance_half(self):
        self.outs = 0
        self.count = [0, 0]
        self.half += 1
        self.runners = ['']*3
        self.get_defense()

    def parse_plays(self):
        for half in self.game:
            parse.parse_half(self, half)

    def parse_debug(self, half, play):
        parsed = parse.parse(self.game[half][play], self)
        return parsed

    def make_sub(self, s):
        self.lineups.make_sub(s, self)
        s.defense = self.get_defense()

    def get_defense(self):
        if self.half % 2 == 0:
            team = 'h'
        else:
            team = 'a'
        self.defense = self.lineups.get_defense(team) #TODO

    # def output(self):
    #     pass

def get_pbp(game_id) -> list:
    """
    extracts pbp text from table

    Parameters
    ----------
    game_id : int
        unique game id

    Returns
    -------
    list
        Play by play text as a list of lists,
        with each sublist containing play by play for a half inning
    """
    table = scrape.get_table('https://stats.ncaa.org/game/play_by_play/' + str(game_id))
    skip = True
    score = False
    plays = []
    game = []
    none = 0
    i = 0
    half = 1
    for element in table:
        for e in element:
            if e.text == "Score":
                score = True
            elif score:
                skip = False
                score = False
                i = -1
            elif not skip:
                i += 1
                if e.text is None:
                    none += 1
                elif e.text[0:3] == " R:":
                    skip = True
                    none = 0
                    half += 1
                    game.append(clean_plays(plays))
                    plays = []
                elif half % 2 != 0:
                    if i % 3 == 0:
                        plays.append(e.text)
                        none = 0
                    if none > 2:
                        half += 1
                        none = 0
                        game.append(clean_plays(plays))
                        plays = []
                if half %2 == 0:
                    if (i-2) % 3 == 0:
                        plays.append(e.text)
                        none = 0
    return game

def clean_plays(plays) -> list:
    new_plays = []
    for play in plays:
        if not 'No play.' in play:
            if 'fielder\'s choice' in play:
                fc = re.search(r"(out at first [a-z0-9]{1,2} to [a-z0-9]{1,2}, )reached on a fielder's choice", play)
                if not fc is None:
                    play = play.replace(fc.group(1), '')
            play = play.replace('did not advance', 'no advance')
            new_plays.append(play.replace('3a', ':').replace(';', ':').replace('a dropped fly', 'an error').replace('a muffed throw', 'an error'))
    return new_plays
