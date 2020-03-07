import scrape
import pandas as pd

class Lineups:
    def __init__(self, game_id):
        [[self.a_lineup, self.a_sub], [self.h_lineup,
            self.h_sub]] = get_lineups(game_id)

    def make_sub(self, s, g):
        lu = self.a_lineup if s.team == 'a' else self.h_lineup
        subs = self.a_sub if s.team == 'a' else self.h_sub
        names = g.names.a_names if s.team == 'a' else g.names.h_names
        if '/' in s.sub_in:
            if len([p.name for p in lu if p.pos == 'p']) > 1:
                lu = lu[0:9]
        if s.pos == 'pr':
            for r in g.runners:
                if r != '':
                    if r.name == s.sub_out:
                        r.name = s.sub_in
        # sub_full = rev_dict(s.sub_in, names)
        index = find_player_index(lu, s.sub_in)
        if index == -1:
            sub_index = find_player_index(subs, s.sub_in)
            if s.pos == 'p' and find_pos_index(lu, 'p') == -1:
                lu.append(subs[sub_index])
            else:
                if s.sub_out == '':
                    for player in lu:
                        if player.sub == s.sub_in:
                            sub_out_full = player.name
                out_index = find_player_index(lu, s.sub_out)
                lu[out_index] = subs[sub_index]
        else:
            if s.pos in lu[index].switch:
                lu[index].pos = s.pos
        if s.team == 'a':
            self.a_lineup = lu
        else:
            self.h_lineup = lu


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


def find_player_index(lu, name):
    for i in range(0,len(lu)):
        if lu[i].name == name:
            return i
    return -1

def find_pos_index(lu, pos):
    for i in range(0,len(lu)):
        if lu[i].pos == pos:
            return i
    return -1

def get_names(lu):
    names = []
    for batter in lu:
        names.append(batter.name)
    return names

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
