import modules.scrape as scrape
import pandas as pd
import modules.player as player
import modules.names as names


class Lineup:
    """
    Contains lists of player objects
    """

    def __init__(self, game_id, team):
        # TODO: add player id
        self.game_id = game_id
        self.lineup = None
        self.subs = None
        self.order = 1
        self.team = team
        self.get_lineups()

    def get_lineups(self):
        """Assigns lists of player objects to Lineup object attributes based on game_id and team

        :param game_id: game ID
        :type game_id: int
        """
        [players, positions, ids] = scrape.get_lu_table(self.game_id)
        lu = compile_lineups(players, positions, ids, self.team)
        self.lineup = lu['lineup']
        self.subs = lu['subs']

    def get_batter(self, half, order):
        """Get the batter at a particular position in the batting order given top/bottom of inning

        :param half: 0 for top or 1 for bottom
        :type half: int
        :param order: in the range 1-9 to represent batting order
        :type order: int
        :return: name of the player in that position in the lineup
        :rtype: str
        """
        if half == 0:
            return self.a_lineup[order-1].name
        else:
            return self.h_lineup[order-1].name

    def all_names(self, team):
        if team == 1:
            return self.h_lineup['name'].to_list() + self.h_subs
        elif team == 0:
            return self.a_lineup['name'].to_list() + self.a_subs

    def get_defense(self):
        pos_list = ['p', 'c', '1b', '2b', '3b', 'ss', 'lf', 'cf', 'rf']
        d = []
        l = self.lineup
        for p in pos_list:
            if len([player.pos for player in l if player.pos == p]) > 0:
                d.append([player.id for player in l if player.pos == p][0])
            else:
                d.append('')
        return d

    def make_sub(self, sub):
        """makes lineup change based on Sub object

        :param sub: [description]
        :type sub: [type]
        """
        [lu, subs] = [self.lineup, self.subs]
        # print([s.__dict__ for s in subs])
        if 'PositionSwitch' in str(type(sub)):
            for player in lu:
                if player.name == sub.player:
                    player.pos = sub.pos
                    player.switch.remove(sub.pos)

        elif 'OffensiveSub' in str(type(sub)):
            lu_idx = find_player_index(lu, sub.sub)
            sub_idx = find_player_index(subs, sub.player)
            if subs[sub_idx].status == 'removed':
                print('ILLEGAL SUB')
            lu[lu_idx].status = 'removed'
            subs.append(lu.pop(lu_idx))
            lu.insert(lu_idx, subs[sub_idx])
            # TODO: Pinch runner functionality

        elif 'DefensiveSub' in str(type(sub)):
            lu_idx = find_player_index(lu, sub.sub)
            sub_idx = find_player_index(subs, sub.player)
            if subs[sub_idx].status == 'removed':
                print('ILLEGAL SUB')
            lu[lu_idx].status = 'removed'
            subs.append(lu.pop(lu_idx))
            lu.insert(lu_idx, subs[sub_idx])

        elif 'Removal' in str(type(sub)):
            lu_idx = find_player_index(lu, sub.sub)
            lu[lu_idx].status = 'removed'
            subs.append(lu.pop(lu_idx))

        [self.lineup, self.subs] = [lu, subs]

        # if s.sub_in == -1:
        #     print(s.__dict__)
        # if '/' in s.sub_in:
        #     if len([p.name for p in lu if p.pos == 'p']) > 1:
        #         lu = lu[0:9]
        # if s.pos == 'pr':
        #     for r in g.runners:
        #         if r != '':
        #             if r.name == s.sub_out:
        #                 r.name = s.sub_in
        # # sub_full = rev_dict(s.sub_in, names)
        # index = find_player_index(lu, s.sub_in)
        # if index == -1:
        #     sub_index = find_player_index(subs, s.sub_in)
        #     if s.pos == 'p' and find_pos_index(lu, 'p') == -1:
        #         lu.append(subs[sub_index])
        #     else:
        #         out_index = find_player_index(lu, s.sub_out)
        #         if out_index == -1:
        #             out_index = find_pos_index(lu, s.pos)
        #         lu[out_index] = subs[sub_index]
        # else:
        #     if s.pos in lu[index].switch:
        #         lu[index].pos = s.pos
        # if s.team == 'a':
        #     self.a_lineup = lu
        # else:
        #     self.h_lineup = lu

    def add_names(self, names):
        for player in self.lineup:
            player.match_pbp_name(names)
        for player in self.subs:
            player.match_pbp_name(names)


def find_player_index(lu, name):
    for i in range(0, len(lu)):
        if lu[i].name == name:
            return i
    return -1


def find_pos_index(lu, pos):
    for i in range(0, len(lu)):
        if lu[i].pos == pos:
            return i
    return -1


def get_names(lu):
    names = []
    for batter in lu:
        names.append(batter.name)
    return names


# def get_index(list, type):
#     if type == "l":
#         return [i for i, s in enumerate(list) if not '\xa0' in s]
#     elif type == "s":
#         return [i for i, s in enumerate(list) if '\xa0' in s]
#
# def list_index(list, index):
#     return [list[i] for i in index]

def compile_lineups(players, pos, id_list, team):
    """given lists of names and positions returns two lists populated with Player objects

    :param names: player names from box score
    :type names: list
    :param positions: player positions from box score
    :type positions: list
    :return: dict containing a 'lineup' list of Players and 'subs' list of Players
    :rtype: dict
    """
    lu = []
    subs = []
    names = players[team]
    positions = pos[team]
    ids = id_list[team]
    for n in range(len(names)):
        if names[n][-1] == ' ':
            names[n] = names[n][0:-1]
    for i in range(0, len(names)):
        names[i] = names[i].replace('Ã±', 'n')
        if '\xa0' in names[i]:
            if not i == 0:
                if not '\xa0' in names[i-1]:
                    j = i + 1
                    while '\xa0' in names[j]:
                        j += 1
                    sub_out = names[j]
                    sub_out_id = ids[j]
                else:
                    sub_out = names[i-1]
                    sub_out_id = ids[i-1]
            else:
                j = i + 1
                while '\xa0' in names[j]:
                    j += 1
                sub_out = names[j]
                sub_out_id = ids[j]
            subs.append(player.Player(names[i].replace('\xa0', ''), ids[i], positions[i][0], positions[i][1:] if len(
                positions) > 1 else [], len(lu) + 1, sub_out.replace('\xa0', ''), sub_out_id, 'available', team))
        else:
            lu.append(player.Player(names[i], ids[i], positions[i][0], positions[i][1:] if len(
                positions) > 1 else [], len(lu) + 1, '', '', 'entered', team))
    return {"lineup": lu, "subs": subs}
