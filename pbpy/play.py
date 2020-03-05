import pandas as pd
import dict
import names
import re

class Play:
    def __init__(self, text, game):
        self.text = text
        self.g = game
        self.off_team = 'a' if self.g.half % 2 == 0 else 'h'
        [self.event, self.code] = get_event(self.text, '')
        self.primary = self.g.names.match_name(self.off_team, get_primary(text, self.event[0]), 'p')[0]
        self.events = []
        self.batter = self.g.lineups.get_batter(self.g)
        parts = self.split_play()
        if self.primary == self.batter:
            self.events.append(BatEvent(parts.pop(0)))
            self.type = 'b'
        else:
            self.type = 'r'
        for p in parts:
            if not p == '' and not ' no advance' in p:
                self.events.append(RunEvent(p))
        self.match_players()
        self.get_info()

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
        off_names = self.g.names.h_names if self.g.half % 2 == 1 else self.g.names.a_names
        players = {name: new_text.index(name) for name in off_names.values() if name in new_text}
        sort_players = {k: v for k, v in sorted(players.items(), key=lambda item: item[1])}
        if len(sort_players) > 1:
            for name in list(sort_players.keys())[1:]:
                split = new_text.split(name)
                parts.append(split[0])
                new_text = name + split[1]
            parts.append(new_text)
        else:
            parts = [new_text]
        return parts


class BatEvent:
    def __init__(self, text):
        self.text = text
        [self.event, self.code] = get_event(self.text, 'b')
        [self.det_event, self.det_abb] = get_det_event(self.text, 'b')
        self.ev_code = dict.event_codes[self.code]
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
        loc = [dict.loc_codes[key] for key in dict.loc_codes.keys() if key in self.text]
        if len(loc) > 0:
            return loc[0]
        else:
            if len(self.fielders) > 0:
                return self.fielders[0]
            else:
                return ''

    def get_bat_dest(self):
        return [dict.run_codes[key] for key in dict.run_codes.keys() if key in self.text][-1]



class RunEvent:
    def __init__(self, text):
        self.text = text
        [self.event, self.code] = get_event(self.text, 'r')
        [self.det_event, self.det_abb] = get_det_event(self.text, 'r')
        self.ev_code = dict.event_codes[self.det_abb] if not self.det_abb == '' else ''
        if not self.det_event == '' and self.text.index(self.det_event) < self.text.index(self.event):
            self.player = get_primary(self.text, self.det_event)
        else:
            self.player = get_primary(self.text, self.event)
        self.dest = self.get_run_dest()

    def get_run_dest(self):
        return [dict.run_codes[key] for key in dict.run_codes.keys() if key in self.text][-1]


class Runner:
    def __init__(self, name, g):
        self.name = name
        self.resp = g.defense[0]

def get_event(text, type):
    if type == 'b':
        return [[key, dict.codes[key]] for key in dict.codes.keys() if key in text][0]
    elif type == 'r':
        return [[key, dict.run_codes[key]] for key in dict.run_codes.keys() if key in text][0]
    else:
        e = [[key, dict.codes[key]] for key in dict.codes.keys() if key in text]
        if e == []:
            check = [[key, dict.run_codes[key]] for key in dict.run_codes.keys() if key in text]
            if check == []:
                return 'None'
            return check[0]
        else:
            return e[0]

def get_det_event(text, type):
    e = [[key, dict.mod_codes[key]] for key in dict.mod_codes.keys() if key in text]
    if e == []:
        return ['','']
    else:
        return e[0]



def get_primary(text, event):
    run_txt = [key for key in dict.run_codes.keys() if key in text]
    if not run_txt == []:
        if text.index(run_txt[0]) < text.index(event):
            spl = run_txt[0]
        else:
            if not len(event) == 0:
                spl = event
    else:
        spl = event
    return text.split(' ' + spl)[0]

def get_fielders(text, event):
    return [dict.pos_codes[key] for key in dict.pos_codes.keys() if key in text.split(' ' + event)[1]]
