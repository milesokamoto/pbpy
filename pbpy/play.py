import pandas as pd
import dict
import names

class Play:
    def __init__(self, text, game):
        self.text = text
        self.game = game
        if self.game.half % 2 == 0:
            self.off_team = 'a'
        else:
            self.off_team = 'h'
        self.event = get_event(self.text, '')
        self.primary = self.game.names.match_name(self.off_team, get_primary(text, self.event))
        self.parts = self.text.split(':')
        self.events = []
        self.batter = self.game.lineups.get_batter(self.game)
        if self.primary == self.batter:
            self.events.append(BatEvent(self.parts.pop(0)))
            self.type = 'b'
        else:
            self.type = 'r'
        for p in self.parts:
            if not p == '':
                self.events.append(RunEvent(p))
        self.match_players()

    def match_players(self):
        for e in self.events:
            e.player = self.game.names.match_name(self.off_team, e.player)

class BatEvent:
    def __init__(self, text):
        self.text = text
        [self.event, self.code] = get_event(self.text, 'b')
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
            return self.fielders[0]

    def get_bat_dest(self):
        return [dict.run_codes[key] for key in dict.run_codes.keys() if key in self.text][-1]



class RunEvent:
    def __init__(self, text):
        self.text = text
        [self.event, self.code] = get_event(self.text, 'r')
        self.player = get_primary(self.text, self.event)
        self.end = self.get_run_dest()

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
        e = [[key, dict.codes[key]] for key in dict.codes.keys() if key in text][0]
        if e is None:
            return [[key, dict.run_codes[key]] for key in dict.run_codes.keys() if key in text][0]
        else:
            return e


def get_primary(text, event):
    return text.split(' ' + event[0])[0]


def get_fielders(text, event):
    return [dict.pos_codes[key] for key in dict.pos_codes.keys() if key in text.split(' ' + event)[1]]
