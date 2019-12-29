import pandas as pd
import dict
import names

class Play:
    def __init__(self, play):
        self.play = play
        self.type = get_play_type(self, text)
        self.primary = get_primary(self, text)


    def bat_event(text):
        [event, code] = get_event(text)
        primary = get_primary(text, event)
        return [primary, code]


    def get_event(text):
        return [[key, dict.codes[key]] for key in dict.codes.keys() if key in text][0]


    def get_loc(text):
        return [dict.loc_codes[key] for key in dict.loc_codes.keys() if key in text][0]


    def get_primary(text, event):
        return text.split(' ' + event)[0]


    def get_run(text):
        return [[key, dict.run_codes[key]] for key in dict.run_codes.keys() if key in text][0]


    def get_fielders(text, event):
        return [dict.pos_codes[key] for key in dict.pos_codes.keys() if key in text.split(' ' + event)[1]]


    def get_play_type(self, text):
        pass
    def execute(self):
        pass
