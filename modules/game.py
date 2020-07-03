import re

import pandas as pd

import modules.lineup as lineup
import modules.names as names
import modules.parse as parse
import modules.play as play
import modules.scrape as scrape
import modules.sub as sub

class Game:
    """Object representing one game
    """
    def __init__(self, id):
        self.id = id
        
        #keep track of whether there is an error in parsing the game
        self.error = False

        #keep track of where in the game we are
        self.play = {'play_idx': 0, 'play_of_inn': 0, 'pbp_idx': 0, 'pbp_of_inn': 0}
        # self.play_list_id = scrape.get_game_id('https://stats.ncaa.org/game/box_score/' + id)
        # self.meta = get_info(id) #should be separate db table
        
        #keep track of inning/half/outs/runners/score info
        #Runners could be tracked using ids based on lineup order?
        self.state = {'inning': 1, 'half': 0, 'outs': 0, 'runners': ['','','',''], 'score': [0,0]}
        
        #create lineups based on game id
        self.lineups = lineup.Lineups(self.id) # 2 lineup objects, 2 sub lists

        #scrape the play by play based on id
        self.play_list = get_pbp(self.id)

        #create a dictionary of names to go between the lineup and play by play
        #TODO: what if we kept track of everyone using an id which just pointed to the lineup or whatever
        self.names = names.NameDict(self)

        #add names to lineup object
        self.lineups.add_names(self.names)

        #check subs based on the box score with play by play
        #TODO: clean them up if there's an error
        self.check_subs()

        #remove pbp lines that aren't plays or subs
        self.clean_game()

        #Create play and sub objects for every line of pbp
        self.create_plays()

        #iterate through game
        self.execute_game()


    # def advance_half(self):
    #     self.leadoff_fl = True
    #     self.outs = 0
    #     self.play_of_inn = 0
    #     self.inn_pbp_no = 0
    #     self.count = [0, 0]
    #     self.state['half'] += 1
    #     self.runners = ['']*4
    #     if len(self.play_list[self.state['half']]) > 1:
    #         if not parse.get_type(self.play_list[self.state['half']][0])[0] == 's':
    #             self.defense = self.get_defense()


    def check_lineups(self):
        h = check_lineup(self.lineups.h_lineup)
        a = check_lineup(self.lineups.a_lineup)
        return h and a

    def check_subs(self):
        """Matches substitutions in play by play to box score and raises errors for mismatches
        """
        sub_regex = r"^([A-Za-z,\. '-]*?(?= [a-z])|\/) (pinch (?:hit|ran)|to [0-9a-z]{1,2})* *(?:for ([A-Za-z,\. '-]*?)\.$)*"
        sub_plays = [play for half in self.play_list for play in half if not re.search(sub_regex, play).group(2) is None]
        subs_from_box = {}

        for player in self.lineups.a_lineup:
            if len(player.switch) > 0:
                for pos in player.switch:
                    s = {'name':player.name, 'pos':pos, 'team':'a'}
                    subs_from_box[len(subs_from_box)] = s

        for player in self.lineups.a_subs:
            if len(player.switch) > 0:
                for pos in player.switch:
                    s = {'name':player.name, 'pos':pos, 'team':'a'}
                    subs_from_box[len(subs_from_box)] = s

        for player in self.lineups.a_subs:
            if not player.sub == '':
                s = {'name':player.name, 'replaces':player.sub, 'team':'a'}
                subs_from_box[len(subs_from_box)] = s

        for player in self.lineups.h_lineup:
            if len(player.switch) > 0:
                for pos in player.switch:
                    s = {'name':player.name, 'pos':pos, 'team':'h'}
                    subs_from_box[len(subs_from_box)] = s

        for player in self.lineups.h_subs:
            if len(player.switch) > 0:
                for pos in player.switch:
                    s = {'name':player.name, 'pos':pos, 'team':'h'}
                    subs_from_box[len(subs_from_box)] = s

        for player in self.lineups.h_subs:
            if not player.sub == '':
                s = {'name':player.name, 'replaces':player.sub, 'team':'h'}
                subs_from_box[len(subs_from_box)] = s

        for i in range(0,len(subs_from_box)):
            team = subs_from_box[i]['team']
            if team == 'a':
                name_list = self.names.a_names
            elif team == 'h':
                name_list = self.names.h_names
            for play in sub_plays:
                [sub_in, pos, sub_out] = sub.parse_sub(play)
                if name_list[subs_from_box[i]['name']] == sub_in:
                    if 'replaces' in subs_from_box[i].keys():
                        if name_list[subs_from_box[i]['replaces']] == sub_out:
                            subs_from_box[i]['text'] = play
                            sub_plays.remove(play)
                    else:
                        if 'pos' in subs_from_box[i].keys():
                            if subs_from_box[i]['pos'] == pos:
                                subs_from_box[i]['text'] = play
                                sub_plays.remove(play)
        
        print(subs_from_box)

        for i in range(0, len(subs_from_box)):
            if not 'text' in subs_from_box[i].keys():
                self.error = True
                print("ERROR: not all subs accounted for")
                print(subs_from_box)
        if len(sub_plays) > 0:
            self.error = True
            print("ERROR: too many subs in pbp")
            print(subs_from_box)
            print(sub_plays)
        
        # burns = [play for half in self.play_list for play in half if '/ ' in play]
        # for b in burns:
            
        self.subs = subs_from_box
        # TODO: handle subs for various types of errors

    def create_plays(self):
        """For each play in the pbp text, create either a play or sub object
        """        
        g = []
        for half in range(0, len(self.play_list)):
            h = []
            for p in self.play_list[half]:
                if parse.get_type(p) == 'p':
                    team = 'a' if half % 2 == 0 else 'h'
                    names = self.names.a_names if team == 'a' else self.names.h_names
                    new_play = play.Play(p, names)
                    new_play.get_type(self.lineups, team)
                    new_play.create_events()
                    h.append(new_play)
                elif parse.get_type(p) == 's':
                    new_sub = None
                    for i in range(0, len(self.subs)):
                        if self.subs[i]['text'] == p:
                            sub_idx = self.subs[i]
                            if not 'replaces' in sub_idx.keys():
                                new_sub = sub.PositionSwitch(sub_idx['team'], sub_idx['name'], sub_idx['pos'], p)
                            elif not((self.state['half'] == 0) ^ (sub_idx['team'] == 'h')):
                                if ' ran ' in p:
                                    sub_type = 'pr'
                                else:
                                    sub_type = 'ph'
                                new_sub = sub.OffensiveSub(sub_idx['team'], sub_idx['name'], sub_idx['replaces'], sub_type, p)
                            else:
                                new_sub = sub.DefensiveSub(sub_idx['team'], sub_idx['name'], sub_idx['replaces'], sub.parse_sub(p)[1], p)
                    if new_sub is None:
                        if '/ ' in p:
                            team = 'a' if half % 2 == 1 else 'h'
                            new_sub = sub.Removal(team, sub.parse_sub(p)[2], p)
                    h.append(new_sub)
            g.append(h)
        self.events = g
        
    def execute_game(self):
        for h in self.events:
            for e in h:
                if "sub" in str(type(e)):
                    self.lineups.make_sub(e)
                    if 'OffensiveSub' in str(type(e)):
                        if e.sub_type == 'pr':
                            for r in self.state['runners']:
                                if not r == '':
                                    if r.name == e.sub:
                                        r.name = e.player
                else:
                    check = self.check_lineups()
                    # print(check)
                    output = self.execute_play(e)
                    # print(output)
            self.state['half'] = (self.state['half']  + 1) % 1
            self.state['runners'] = ['']*4
                    
            
    def execute_play(self, p):
        new_runners = ['']*4
        pitcher = self.lineups.get_defense(self.state['half'])[0]
        # batter = self.lineups.get_batter(self.state['half'], p.order)
        dest = ['']*4

        event_outs = 0

        for e in reversed(p.events):
            print(e.__dict__)
            print('\n')
            if type(e) == play.RunEvent:
                for i in range(1, 4):
                    if self.state['runners'][i] != '':
                        runner = self.state['runners'][i]
                        if runner.name == e.player:
                            dest[i] = e.dest[1] if e.dest[1] == 0 else e.dest[0]
            else:
                r = play.Runner(e.full_name, pitcher)
                if e.code in [17, 18]:
                    r.resp = ''
                self.state['runners'][0] = r
                dest[0] = e.dest[1] if e.dest[1] == 0 else e.dest[0]
        for i in range(0, 4):
            if dest[i] != '':
                if dest[i] in [1,2,3]:
                    new_runners[dest[i]] = self.state['runners'][i]
                elif dest[i] == 4:
                    self.state['score'][self.state['half'] % 2] += 1
                elif dest[i] == 0:
                    event_outs += 1
            else:
                if self.state['runners'][i] != '':
                    new_runners[i] = self.state['runners'][i]
        self.state['runners'] = new_runners
        return True

        # self.output.append(self.get_output(p))
        # print('play no: ' + str(self.play))
        # # print(self.play_list[self.state['half']][self.play_of_inn])

        # if self.leadoff_fl == True:
        #     self.leadoff_fl = False
        # self.runners = new_runners
        # self.dest = ['']*4
        # self.outs += self.event_outs
        # self.event_outs = 0

        # if p.type == 'b':
        #     if p.off_team == 'a':
        #         self.a_order = (self.a_order + 1) % 9
        #     else:
        #         self.h_order = (self.h_order + 1) % 9
        # self.play += 1
        # self.play_of_inn += 1


        # self.sub = []

    def get_output(self, p):
        output = {
        'ncaa_id': self.id,
        'inning': round(self.state['half']/2+.51),
        'half': self.state['half'] % 2,
        'outs': self.outs,
        'balls': self.count[0],
        'strikes': self.count[1],
        'seq': self.seq, # add x if in play
        'a_score': self.score[0],
        'h_score': self.score[1],
        'batter': p.batter,
        'batter_order': self.a_order if self.state['half'] % 2 == 0 else self.h_order, #
        'batter_pos': self.lineups.a_lineup[self.a_order].pos if self.state['half'] % 2 == 0 else  self.lineups.h_lineup[self.h_order].pos, #
        'batter_dest': self.dest[0],
        'batter_play': loc if type(self.last_play.events[0]) == 'play.BatEvent' else '',
        'pitcher': self.defense[0],
        'defense': self.defense[1:],
        'run_1': self.runners[1].name if self.runners[1] != '' else '',
        'run_1_resp': self.runners[1].resp if self.runners[1] != '' else '',
        'run_1_dest': self.dest[1] if self.runners[1] != '' else '',
        'run_1_play': '', #defense
        'run_2': self.runners[2].name if self.runners[2] != '' else '',
        'run_2_resp': self.runners[2].resp if self.runners[2] != '' else '',
        'run_2_dest': self.dest[2] if self.runners[2] != '' else '',
        'run_2_play': '',
        'run_3': self.runners[3].name if self.runners[3] != '' else '',
        'run_3_resp': self.runners[3].resp if self.runners[3] != '' else '',
        'run_3_dest': self.dest[3] if self.runners[3] != '' else '',
        'run_3_play': '',
        'full_event': p.event, #
        'leadoff_fl': 1 if self.play_of_inn == 0 else 0,
        'event_text': p.events[0].det_abb,
        'event_cd': p.events[0].ev_code, #
        'bat_event_fl': 1 if p.type == 'b' else 0, #
        'sac_fl': 1 if 'SAC' in p.text else 0, #
        'event_outs': self.event_outs,
        'rbi': 1 if ', RBI' in p.text else int(p.text.split(' RBI')[0][-1]) if 'RBI' in p.text else 0,
        'fielder': '', #
        'batted_ball': '', #
        'errors': {}, #Need to add dropped foul
        'h_fl': 1 if p.events[0].ev_code in [20, 21, 22, 23] else 0,
        'ab_fl': 1 if p.events[0].ev_code in [2, 3, 18, 19, 20, 21, 22, 23] else 0,
        'sb_fl': 1 if 'stole' in p.text else 0,
        'cs_fl': 1 if 'caught stealing' in p.text else 0,
        'pk_fl': 1 if 'picked off' in p.text else 0,
        'sub_fl': self.sub, # new, position, removed,
        'po': {}, #,
        'assist': {},
        'event_no': self.play+1, #
        'pbp_text': p.text
        }
        return output

    

    # def parse_plays(self):
    #     for half in self.play_list:
    #         parse.parse_half(self, half)

    # def parse_debug(self, half, play):
    #     while self.state['half'] < half:
    #         parse.parse_half(self, self.play_list[self.state['half']])
    #         print('parsing half ' + str(self.state['half']))
    #     while self.inn_pbp_no <= play:
    #         parsed = parse.parse(self.play_list[self.state['half']][self.inn_pbp_no], self)
    #         print('parsing play ' + str(self.inn_pbp_no))
    #         print(self.play_list[self.state['half']][self.inn_pbp_no-1])
    #     return parsed

    # def parse_step(self):
    #     parsed = parse.parse(self.play_list[self.state['half']][self.inn_pbp_no], self)
    #     print('parsing play ' + str(self.inn_pbp_no))
    #     print(self.play_list[self.state['half']][self.inn_pbp_no-1])
    #     return parsed

    # def make_sub(self, s):
    #     # if s.pos == "ph":
    #     #     if self.lineups.get_batter(self) != s.sub_out:
    #     #         return
    #     self.lineups.make_sub(s, self)
    #     self.sub.append([s.sub_in, s.pos, s.sub_out])

    def get_defense(self):
        if self.state['half'] % 2 == 0:
            team = 'h'
        else:
            team = 'a'
        return self.lineups.get_defense(team)

    def all_plays(self, team):
        out = []
        for i in range(0, len(self.play_list)):
                x = self.play_list[i]
                for p in x:
                    if team == 'h' and i % 2 == 1 or team == 'a' and i % 2 == 0 or not team in ('h', 'a'):
                        out.append(p)
        return out

    def clean_game(self):

        for i in range(0, len(self.play_list)):
            delete = []
            half = self.play_list[i]
            for j in range(0, len(half)):
                p = half[j]
                h = [name for name in self.names.h_names.values() if name + ' ' in p]
                a = [name for name in self.names.a_names.values() if name + ' ' in p]
                if len(h) == 0 and len(a) == 0 and not '/ ' in p:
                    delete.append(j)
                if 'failed pickoff attempt.' in p:
                    delete.append(j)
            deleted = 0
            for k in delete:
                self.play_list[i].pop(k-deleted)
                deleted += 1

    # def output(self):
    #     pass

def get_pbp(game_id) -> list:
    """ extracts pbp text from table

    :param game_id: unique game id
    :type game_id: int
    :return: Play by play text as a list of lists, with each sublist containing play by play for a half inning
    :rtype: list
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
                if half % 2 == 0 and not e.text is None:
                    if (i-2) % 3 == 0:
                        plays.append(e.text)
                        none = 0
    return game

def clean_plays(plays) -> list:
    new_plays = []
    for play in plays:
        if not 'No play.' in play:
            if play[0:3] == 'for':
                play = '/ ' + play
            if 'fielder\'s choice' in play:
                fc = re.search(r"(out at first [a-z0-9]{1,2} to [a-z0-9]{1,2}, )reached on a fielder's choice", play)
                if not fc is None:
                    play = play.replace(fc.group(1), '')
            play = play.replace('did not advance', 'no advance')
            new_plays.append(play.replace('3a', ':').replace(';', ':').replace(': ', ':').replace('a muffed throw', 'an error'))
    return new_plays

def check_lineup(lineup):
    # Rules:
    # must have all defensive positions
    # must have numbers 1-9 in order (10 is pitcher)
    # if dh position, then must have 10 if not then must only have 9
    # no removed players allowed
    pos_list = ['p', 'c', '1b', '2b', '3b', 'ss', 'lf', 'cf', 'rf', 'dh']
    order_list = list(range(1,11))
    pinch = 0
    for player in lineup:
        if player.pos in pos_list:
            pos_list.remove(player.pos)
        elif player.pos in ['pr', 'ph']:
            pinch += 1
        else:
            print("ERROR: multiple players listed at " + player.pos)
            return False
        if player.order in order_list:
            order_list.remove(player.order)
        else:
            print("ERROR: multiple players listed at " + player.order)
            return False
    if 10 in order_list and not 'dh' in pos_list:
        print("ERROR: missing position " + str(pos_list))
        return False
    if len(order_list) == 0 and not len(pos_list) - pinch == 0:
        print("ERROR: missing position " + str(pos_list))
        return False
    if len(pos_list) == 0 and not len(order_list) == 0:
        print("ERROR: missing order " + str(order_list))
        return False
    if len(order_list) > 0 and not order_list == [10] :
        print("ERROR: missing order " + str(order_list))
        return False
    if len(pos_list) > 0 and not pos_list == ['dh'] :
        print("ERROR: missing order " + str(order_list))
        return False
    return True
