import scrape
import pandas as pd

def get_lineups(game_id):
    player = False
    pos = False
    lineup = []
    away = []
    home = []
    away_pos = []
    home_pos = []
    pos_list = []
    team = 0
    pos_team = 0
    i = 0
    j = 0
    skip = True
    table = scrape.get_table('https://stats.ncaa.org/game/box_score/' + str(game_id))
    for element in table:
        j = 0
        for row in element:
            i = 0
            for cell in row:
                i += 1
                if i == 1 and not cell.text is None:
                    if cell.text == "Fielding":
                        skip = False
                    elif not skip:
                        if not '\n' in cell.text:
                            lineup.append(cell.text)
            j += 1
            if j == 2:
                if row.text == "Pos":
                    pos = True
                elif pos and row.text == None:
                    pos = False
                    if pos_team == 0:
                        away_pos = pos_list
                        away = lineup
                        pos_team = 1
                    else:
                        home_pos = pos_list
                        home = lineup
                    pos_list = []
                    lineup = []
                elif pos:
                    pos_list.append(row.text)
    return compile_lineups(away, away_pos, home, home_pos)

def get_index(list, type):
    if type == "l":
        return [i for i, s in enumerate(list) if not '\xa0' in s]
    elif type == "s":
        return [i for i, s in enumerate(list) if '\xa0' in s]

def list_index(list, index):
    return [list[i] for i in index]

def compile_lineups(away, away_pos, home, home_pos):
    a_lu = list_index(away, get_index(away, 'l'))
    a_lu_pos = list_index(away_pos, get_index(away, 'l'))
    a_sub = [s.replace('\xa0', '') for s in list_index(away, get_index(away, 's'))]
    h_lu = list_index(home, get_index(home, 'l'))
    h_lu_pos = list_index(home_pos, get_index(home, 'l'))
    h_sub = [s.replace('\xa0', '') for s in list_index(home, get_index(home, 's'))]
    away_lu = pd.DataFrame(a_lu, a_lu_pos)
    home_lu = pd.DataFrame(h_lu, h_lu_pos)
    return[away_lu, a_sub, home_lu, h_sub]
