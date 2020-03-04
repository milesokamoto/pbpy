import scrape
import pandas as pd

class Lineups:
    def __init__(self, game_id):
        [[self.a_lineup, self.a_sub], [self.h_lineup,
            self.h_sub]] = get_lineups(game_id)

    def make_sub(self, s, g):
        # lu = self.a_lineup if s.team == 'a' else self.h_lineup
        # if '/' in s.sub_in:
        #     if len(lu[lu['pos']=='P']) > 1:
        #         lu = lu[0:9]
        # if s.pos == 'pr':
        #     for r in g.runners:
        #         if r != '':
        #             if r.name == s.sub_out:
        #                 r.name = s.sub_in
        # if s.pos == 'ph':
        #     order = g.a_order if s.team == 'a' else g.h_order
        #     if s.sub_out is None:
        #         lu.iloc[order]['name'] = s.sub_in
        #         lu.iloc[order]['pos'] = 'PH'
        #     else:
        #         if not len(lu.loc[lu['name'] == s.sub_out, 'name']) > 0:
        #             lu = self.a_lineup if s.team == 'h' else self.h_lineup
        #         lu.loc[lu['name'] == s.sub_out, 'name'] = s.sub_in
        #         lu.loc[lu['name'] == s.sub_in, 'pos'] = s.pos.upper()
        # elif s.sub_out is None:
        #     lu.loc[lu['pos'] == s.pos.upper(), 'pos'] = ''
        #     lu.loc[lu['name'] == s.sub_in, 'pos'] = s.pos.upper()
        # elif len(lu.loc[lu['name'] == s.sub_in, 'name']) > 0:
        #     lu.loc[lu['name'] == s.sub_in, 'pos'] = s.pos.upper()
        # else:
        #     lu.loc[lu['name'] == s.sub_out, 'name'] = s.sub_in
        #     lu.loc[lu['name'] == s.sub_in, 'pos'] = s.pos.upper()
        # if s.team == 'a':
        #     self.a_lineup = lu
        # elif s.team == 'h':
        #     self.h_lineup = lu
        pass


    def get_batter(self, game):
        if game.half % 2 == 0:
            return game.lineups.a_lineup[game.a_order].name
        else:
            return game.lineups.h_lineup[game.h_order].name

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
            if len([player.pos for player in l if player.pos == p]) > 0:
                d.append([player.name for player in l if player.pos == p][0])
            else:
                d.append('')
        return d


def get_lineups(game_id):
    [players, positions] = scrape.get_lu_table('https://stats.ncaa.org/game/situational_stats/' + str(game_id))
    return [compile_lineups(players[0], positions[0]), compile_lineups(players[1], positions[1])]

# def get_index(list, type):
#     if type == "l":
#         return [i for i, s in enumerate(list) if not '\xa0' in s]
#     elif type == "s":
#         return [i for i, s in enumerate(list) if '\xa0' in s]
#
# def list_index(list, index):
#     return [list[i] for i in index]

def compile_lineups(names, positions):
    lu = []
    subs = []
    for i in range(0, len(names)):
        if names[i][-1] == ' ':
            names[i] = names[i][0:-1]
        if '\xa0' in names[i]:
            if not i == 0:
                if not '\xa0' in names[i-1]:
                    j = i + 1
                    while '\xa0' in names[j]:
                        j += 1
                    sub_out = names[j]
                else:
                    sub_out = names[i-1]
            else:
                j = i + 1
                while '\xa0' in names[j]:
                    j += 1
                sub_out = names[j]
            subs.append(Player(names[i].replace('\xa0', ''), positions[i][0], positions[i][1:] if len(positions) > 1 else [], len(lu) + 1, sub_out.replace('\xa0', '')))
        else:
            lu.append(Player(names[i], positions[i][0], positions[i][1:] if len(positions)>1 else [], len(lu) + 1, ''))
    return [lu, subs]

class Player:
    def __init__(self, name, pos, switch, order, sub):
        self.name = name
        self.pos = pos
        self.switch = switch
        self.order = order
        self.sub = sub
