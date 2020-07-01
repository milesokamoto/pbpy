import re

import pandas as pd

import modules.names as names
import modules.ref as ref


class Play:
    def __init__(self, text, names):
        self.text = text
        self.names = names
        self.play_names = play_names(text, names)
        self.parts = self.split_play()
        self.order = 0

        # print(self.parts)
        # self.create_events()
        

        # self.state_before = state
        # self.state_after = {'inning': 0, 'half': 0, 'outs': 0, 'runners': '000'}

        # self.play_info = {}
 
        # self.off_team = 'a' if self.g.half == 0 else 'h'

        # [self.event, self.code] = get_event(self.text, '')
        
        # self.events = []
        # self.batter = self.g.lineups.get_batter(self.g)
        # parts = self.split_play()
        # # print('parts: ' + str(parts))
        # if self.primary == self.batter:
        #     self.events.append(BatEvent(parts.pop(0)))
        #     self.type = 'b'
        # else:
        #     self.type = 'r'
        # for p in parts:
        #     if not p == '' and not ' no advance' in p:
        #         self.events.append(RunEvent(p))
        # self.match_players()
        # self.get_info()
    
    def create_events(self):
        for i in range(0, len(parts)):
            pass

    def match_players(self):
        for e in self.events:
            e.player = self.g.names.match_name(self.off_team, e.player, 'p')[0]

    def get_info(self):
        if '(' in self.text:
            count = re.search(r'[0-3]-[0-2]', self.text).group(0)
            self.g.count = count.split('-')
            self.g.seq = re.search(r'[KFBS]*(?=\))', self.text).group(0)

    def split_play(self):
        new_text = self.text
        parts = []
        splits = list(self.play_names.keys())
        for i in range(0, len(splits)):
            name = splits[i]
            split = new_text.split(splits[i] + " ")
            new_text = split[0]
            player_text = split[1]
            parts.insert(0, {'player': name, 'text': player_text})
        return parts
    
    def get_type(self, lineups, team):
        lu = lineups.a_lineup if team == 'a' else lineups.h_lineup
        sub = lineups.a_subs if team == 'a' else lineups.h_subs
        self.order = lineups.a_order if team == 'a' else lineups.h_order
        order_names = [player.pbp_name for player in lu if player.order == self.order]
        order_names.extend([player.pbp_name for player in sub if player.order == self.order])
        print(order_names)
        if self.parts[0]['player'] in order_names:
            self.type = 'b'
            if team == 'a':
                lineups.a_order = self.order % 9 + 1
            else:
                lineups.h_order = self.order % 9 + 1
        else:
            self.type = 'r'


class BatEvent:
    def __init__(self, text):
        self.text = text
        [self.event, self.code] = get_event(self.text, 'b')
        [self.det_event, self.det_abb] = get_det_event(self.text, 'b')
        self.ev_code = ref.event_codes[self.code]
        self.player = get_primary(self.text, self.event)
        self.fielders = get_fielders(text, self.event)
        self.loc = self.get_loc()
        self.dest = self.get_bat_dest()
        self.correct_fielders()

    def correct_fielders(self):
        if self.event == 'grounded out':
            if len(self.fielders) == 1:
                self.fielders.append(3)

    def get_loc(self):
        loc = [ref.loc_codes[key] for key in ref.loc_codes.keys() if key in self.text]
        if len(loc) > 0:
            return loc[0]
        else:
            if len(self.fielders) > 0:
                return self.fielders[0]
            else:
                return ''

    def get_bat_dest(self):
        return [ref.run_codes[key] for key in ref.run_codes.keys() if key in self.text][-1]

class RunEvent:
    def __init__(self, text):
        self.text = text
        [self.event, self.code] = get_event(self.text, 'r')
        [self.det_event, self.det_abb] = get_det_event(self.text, 'r')
        self.ev_code = ref.event_codes[self.det_abb] if not self.det_abb == '' else ''
        if not self.det_event == '' and self.text.index(self.det_event) < self.text.index(self.event):
            self.player = get_primary(self.text, self.det_event)
        else:
            self.player = get_primary(self.text, self.event)
        self.dest = self.get_run_dest()

    def get_run_dest(self):
        return [ref.run_codes[key] for key in ref.run_codes.keys() if key in self.text][-1]


class Runner:
    def __init__(self, name, g):
        self.name = name
        self.resp = g.defense[0]

def get_event(text, type):
    parts = []
    new_text = text
    if type == 'b':
        events = {key: text.index(key) for key in ref.codes.keys() if key in text}
        sort_events = {k: v for k, v in sorted(events.items(), key=lambda item: item[1])}
        return [list(sort_events.keys())[0], ref.codes[list(sort_events.keys())[0]]]
    elif type == 'r':
        return [[key, ref.run_codes[key]] for key in ref.run_codes.keys() if key in text][0]
    else:
        events = {key: text.index(key) for key in ref.codes.keys() if key in text}
        if len(events) > 0:
            sort_events = {k: v for k, v in sorted(events.items(), key=lambda item: item[1])}
            events = [list(sort_events.keys())[0], ref.codes[list(sort_events.keys())[0]]]
        if events == {}:
            check = [[key, ref.run_codes[key]] for key in ref.run_codes.keys() if key in text]
            if check == []:
                return 'None'
            return check[0]
        else:
            return events

def get_det_event(text, type):
    e = [[key, ref.mod_codes[key]] for key in ref.mod_codes.keys() if key in text]
    if e == []:
        return ['','']
    else:
        return e[0]

def get_primary(text, event):
    run_txt = [key for key in ref.run_codes.keys() if key in text]
    if not run_txt == []:
        if text.index(run_txt[0]) < text.index(event):
            spl = run_txt[0]
        else:
            if not len(event) == 0:
                spl = event
    else:
        spl = event
    return text.split(' ' + spl)[0]

def play_names(text, names):
    """get player names and indexes within the play by play strings

    :param text: play by play text
    :type text: str
    :param names: name directory of offensive team
    :type names: dict
    """    
    players = {name: text.index(name) for name in names.values() if name + ' ' in text}
    return({k: v for k, v in sorted(players.items(), key=lambda item: item[1], reverse=True)})

def get_fielders(text, event):
    return [ref.pos_codes[key] for key in ref.pos_codes.keys() if key in text.split(' ' + event)[1]]

