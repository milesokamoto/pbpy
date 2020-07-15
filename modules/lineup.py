import modules.scrape as scrape
import pandas as pd
import modules.player as player
import modules.names as names


class Lineup:
    """
    Contains lists of player objects
    """

    def __init__(self, game_id, team):
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
        return self.lineup[order-1].id

    def all_names(self):
            return self.lineup['name'].to_list() + self.subs['name'].to_list() 

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
        if 'PositionSwitch' in str(type(sub)):
            done = False
            for player in lu:
                if player.id == sub.player:
                    done = True
                    player.switch.append(player.pos)
                    player.pos = sub.pos
                    if sub.pos in player.switch:
                        player.switch.remove(sub.pos)
            if not done:
                sub_idx = find_player_index(subs, sub.player)
                if sub.pos == 'p':
                    subs[sub_idx].status = 'entered'
                    if not len([s for s in lu if s.pos == 'p']) > 0:
                        subs[sub_idx].order = 10
                    lu.append(subs.pop(sub_idx))
                else:
                    print("ERROR: NOT SURE WHAT TO DO WITH SUB")
                    print(sub.__dict__)

        elif 'OffensiveSub' in str(type(sub)):
            lu_idx = find_player_index(lu, sub.sub)
            sub_idx = find_player_index(subs, sub.player)
            if sub_idx is None:
                print("ERROR: " + str(sub.__dict__))
            else:
                if subs[sub_idx].status == 'removed':
                    print('ILLEGAL SUB')
                if not lu_idx is None:
                    lu[lu_idx].status = 'removed'
                    subs.append(lu.pop(lu_idx))
                    lu.insert(lu_idx, subs.pop(sub_idx))
            # TODO: Pinch runner functionality

        elif 'DefensiveSub' in str(type(sub)):
            lu_idx = find_player_index(lu, sub.sub)
            sub_idx = find_player_index(subs, sub.player)
            if sub_idx is None:
                print("ERROR: " + str(sub.__dict__))
            else:
                if subs[sub_idx].status == 'removed':
                    print('ILLEGAL SUB')
                if not lu_idx is None:  
                    lu[lu_idx].status = 'removed'
                    if lu[lu_idx].order != subs[sub_idx].order:
                        print("ASSUMING ORDER FOR SUB: " + subs[sub_idx].name)
                        subs[sub_idx].order = lu[lu_idx].order
                    for p in lu:
                        if p.pos == subs[sub_idx].pos:
                            p.pos = ''
                    subs.append(lu.pop(lu_idx))
                    lu.insert(lu_idx, subs.pop(sub_idx))

        elif 'Removal' in str(type(sub)):
            lu_idx = find_player_index(lu, sub.sub)
            if not lu_idx is None:
                lu[lu_idx].status = 'removed'
                subs.append(lu.pop(lu_idx))

        [self.lineup, self.subs] = [lu, subs]

def find_player_index(lu, id):
    for i in range(0, len(lu)):
        if lu[i].id == id:
            return i
    return None


def find_pos_index(lu, pos):
    for i in range(0, len(lu)):
        if lu[i].pos == pos:
            return i
    return None

def get_names(lu):
    names = []
    for batter in lu:
        names.append(batter.name)
    return names

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
