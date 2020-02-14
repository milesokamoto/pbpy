import scrape
import pandas as pd

class Lineups:
    def __init__(self, game_id):
        [self.a_lineup, self.a_sub, self.h_lineup,
            self.h_sub] = get_lineups(game_id)

    def make_sub(self, s, g):
        lu = self.a_lineup if s.team == 'a' else self.h_lineup
        if '/' in s.sub_in:
            if len(lu[lu['pos']=='P']) > 1:
                lu = lu[0:9]
        if s.pos == 'pr':
            for r in g.runners:
                if r != '':
                    if r.name == s.sub_out:
                        r.name = s.sub_in
        if s.pos == 'ph':
            order = g.a_order if s.team == 'a' else g.h_order
            if s.sub_out is None:
                lu.iloc[order]['name'] = s.sub_in
                lu.iloc[order]['pos'] = 'PH'
            else:
                if not len(lu.loc[lu['name'] == s.sub_out, 'name']) > 0:
                    lu = self.a_lineup if s.team == 'h' else self.h_lineup
                lu.loc[lu['name'] == s.sub_out, 'name'] = s.sub_in
                lu.loc[lu['name'] == s.sub_in, 'pos'] = s.pos.upper()
        elif s.sub_out is None:
            lu.loc[lu['pos'] == s.pos.upper(), 'pos'] = ''
            lu.loc[lu['name'] == s.sub_in, 'pos'] = s.pos.upper()
        elif len(lu.loc[lu['name'] == s.sub_in, 'name']) > 0:
            lu.loc[lu['name'] == s.sub_in, 'pos'] = s.pos.upper()
        else:
            lu.loc[lu['name'] == s.sub_out, 'name'] = s.sub_in
            lu.loc[lu['name'] == s.sub_in, 'pos'] = s.pos.upper()
        if s.team == 'a':
            self.a_lineup = lu
        elif s.team == 'h':
            self.h_lineup = lu


    def get_batter(self, game):
        if game.half % 2 == 0:
            return game.lineups.a_lineup.iloc[game.a_order]['name']
        else:
            return game.lineups.h_lineup.iloc[game.h_order]['name']

    def all_names(self, team):
        if team == 'h':
            return self.h_lineup['name'].to_list() + self.h_sub
        elif team == 'a':
            return self.a_lineup['name'].to_list() + self.a_sub

    def get_defense(self, team):
        pos_list = ['P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF']
        d = []
        if team == 'h':
            l = self.h_lineup
        elif team == 'a':
            l = self.a_lineup
        for p in pos_list:
            if len(l[l['pos'] == p]) > 0:
                d.append(l[l['pos'] == p]['name'].item())
            else:
                d.append('')
        return d


def get_lineups(game_id):
    [players, positions] = scrape.get_lu_table('https://stats.ncaa.org/game/situational_stats/' + str(game_id))
    return compile_lineups(players[0], positions[0], players[1], positions[1])

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
    a_sub = [s.replace('\xa0', '')
             for s in list_index(away, get_index(away, 's'))]
    # a_sub_pos = [away_pos, get_index(away, 's')]

    h_lu = list_index(home, get_index(home, 'l'))
    h_lu_pos = list_index(home_pos, get_index(home, 'l'))
    h_sub = [s.replace('\xa0', '')
             for s in list_index(home, get_index(home, 's'))]
    # h_sub_pos = [home_pos, get_index(home, 's'))]
    a_lineup = pd.DataFrame({'name': a_lu, 'pos': a_lu_pos})
    h_lineup = pd.DataFrame({'name': h_lu, 'pos': h_lu_pos})
    return [a_lineup, a_sub, h_lineup, h_sub]
