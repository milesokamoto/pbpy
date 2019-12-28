import scrape
import pandas as pd

class Game:
    def __init__(self, id):
        self.id = id
        self.game = get_pbp(id)
        self.lineups = get_lineups(id)
        self.runners = ['','','']
        self.state = [0,0,0] #balls/strikes/outs

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
        new_plays.append(play.replace('3a', ':').replace(';', ':').replace('a dropped fly', 'an error').replace('a muffed throw', 'an error'))
    return new_plays
