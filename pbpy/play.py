import pandas as pd
import dict
import names

class Play:
    def __init__(self, text, game):
        self.play = text
        self.primary = get_primary(text)
        self.type = get_play_type()

        # self.type = get_play_type(self, text)
        self.event = self.get_event()


        # self.secondaries = get_secondaries(self, text)

    def execute(self):
        pass

def bat_event(self):
    [event, code] = get_event(self.play)
    primary = get_primary(self.play, event)
    return [primary, code]


def get_event(players):
    return [[key, dict.codes[key]] for key in dict.codes.keys() if key in self.play][0]


def get_loc(play):
    return [dict.loc_codes[key] for key in dict.loc_codes.keys() if key in text][0]


def get_primary(play, event):
    return play.split(' ' + event)[0]


def get_secondaries(text, event):
    return text.split(':')[1:]


def get_run(text):
    return [[key, dict.run_codes[key]] for key in dict.run_codes.keys() if key in text][0]


def get_fielders(text, event):
    return [dict.pos_codes[key] for key in dict.pos_codes.keys() if key in text.split(' ' + event)[1]]


def get_play_type(self, text):
    pass


def get_run_dest(self):
    pass
