import re

import pandas as pd

import modules.names as names
import modules.ref as ref


class Play:
    def __init__(self, text, names):
        self.text = text
        self.play_names = play_names(text, names)
        self.parts = self.split_play()
        self.order = 0

        # print(self.parts)
        

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
        if self.parts[0]['player'] in order_names:
            self.type = 'b'
            if team == 'a':
                lineups.a_order = self.order % 9 + 1
            else:
                lineups.h_order = self.order % 9 + 1
        else:
            self.type = 'r'

    def create_events(self):
        self.events = []
        if self.type == 'b':
            self.events.append(BatEvent(self.parts[0]))
            if len(self.parts) > 1:
                for part in self.parts[1:]:
                    self.events.append(RunEvent(part))
        else:
            for part in self.parts:
                self.events.append(RunEvent(part))

class BatEvent:
    def __init__(self, part):
        self.player = part['player']
        self.text = part['text']
        self.deconstruct_text()



        # [self.event, self.code] = get_event(self.text, 'b')
        # [self.det_event, self.det_abb] = get_det_event(self.text, 'b')
        # self.ev_code = ref.event_codes[self.code]
        # self.player = get_primary(self.text, self.event)
        # self.fielders = get_fielders(text, self.event)
        # self.loc = self.get_loc()
        # self.dest = self.get_bat_dest()
        # self.correct_fielders()

    def deconstruct_text(self):
        pbp = self.text
        self.get_info()
        pbp = pbp.split('(')[0]
        if ', RBI' in pbp:
            self.rbi = 1
            pbp = pbp.split(', RBI')[0]
        elif ' RBI' in pbp:
            self.rbi = int(pbp.split(' RBI')[0][-1])
            pbp = pbp.split(', ' + str(self.rbi) + ' RBI')[0]
        else:
            self.rbi = 0
            
        self.flags = get_flags(pbp)
        if len(self.flags) > 0:
            pbp = pbp.split(', ' + self.flags[0])[0]

        run = get_run(pbp)
        if len(run) > 1:
            pbp = pbp.split(run[1])[0]
        self.dest = ref.run_codes[run[-1]]
        
        loc = get_loc(pbp)
        if len(loc) > 0:
            self.bb_loc = ref.loc_codes[loc[0]]
        #TODO: Add assists and putouts
        #TODO: Add bb type

        self.event = get_event(pbp)

        print(self.__dict__)
                

    def get_info(self):
        if '(' in self.text:
            #TODO: If count in any of the events, fill in rest with 0-0, otherwise n/a
            count = re.search(r'[0-3]-[0-2]', self.text).group(0)
            self.count = count.split('-')
            self.seq = re.search(r'[KFBS]*(?=\))', self.text).group(0)



    # def correct_fielders(self):
    #     if self.event == 'grounded out':
    #         if len(self.fielders) == 1:
    #             self.fielders.append(3)



def get_run(text):
    run = [key for key in ref.run_codes.keys() if key in text]
    sorted_run = [k for k, v in sorted({r:text.index(r) for r in run}.items(), key=lambda item:item[1])]
    return sorted_run

def get_loc(text):
    loc = [key for key in ref.loc_codes.keys() if key in text]
    sorted_loc = [k for k, v in sorted({l:text.index(l) for l in loc}.items(), key=lambda item:item[1])]
    return sorted_loc

def get_flags(text):
    flag = [key for key in ref.flag_codes.keys() if key in text]
    sorted_flags = [ref.flag_codes[k] for k, v in sorted({l:text.index(l) for l in flag}.items(), key=lambda item:item[1])]
    return sorted_flags

def get_event(text):
    ev = [key for key in ref.mod_codes.keys() if key in text]
    sorted_ev = [k for k, v in sorted({l:text.index(l) for l in ev}.items(), key=lambda item:item[1])]
    return sorted_ev



class RunEvent:
    def __init__(self, part):
        self.player = part['player']
        self.text = part['text']
        self.event = get_event(self.text)
        self.dest = get_run_dest(self.text)
        # [self.event, self.code] = get_event(self.text, 'r')
        # [self.det_event, self.det_abb] = get_det_event(self.text, 'r')
        # self.ev_code = ref.event_codes[self.det_abb] if not self.det_abb == '' else ''
        # if not self.det_event == '' and self.text.index(self.det_event) < self.text.index(self.event):
        #     self.player = get_primary(self.text, self.det_event)
        # else:
        #     self.player = get_primary(self.text, self.event)
        # self.dest = self.get_run_dest()

def get_run_dest(text):
    return [ref.run_codes[key] for key in ref.run_codes.keys() if key in text][-1]


class Runner:
    def __init__(self, name, g):
        self.name = name
        self.resp = g.defense[0]

def find_event(text, type):
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

# def get_det_event(text, type):
#     e = [[key, ref.mod_codes[key]] for key in ref.mod_codes.keys() if key in text]
#     if e == []:
#         return ['','']
#     else:
#         return e[0]

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

