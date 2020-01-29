import scrape
import parse
import pandas as pd
import re
import lineup
import names
import play

class Game:
    def __init__(self, id):
        self.id = id
        # self.game_id = scrape.get_game_id('https://stats.ncaa.org/game/box_score/' + id)
        # self.meta = get_info(id) #should be separate db table
        self.play = 0
        self.play_of_inn = 0
        self.pbp_no = 0
        self.inn_pbp_no = 0
        self.half = 0 # inning is (half/2)+1, top/bottom is even/odd
        self.lineups = lineup.Lineups(self.id) # 2 lineup objects, 2 sub lists
        self.runners = ['']*4
        self.dest = ['']*4
        self.outs = 0
        self.event_outs = 0
        self.count = [0, 0] #balls/strikes/outs
        self.seq = ''
        self.h_order = 0
        self.a_order = 0
        self.score = [0,0]
        self.defense = self.get_defense()
        self.leadoff_fl = True
        self.names = names.NameDict(self.lineups)
        self.game = get_pbp(self.id)
        self.output = []
        self.last_play = []
        self.sub = []

    def advance_half(self):
        self.leadoff_fl = True
        self.outs = 0
        self.play_of_inn = 0
        self.inn_pbp_no = 0
        self.count = [0, 0]
        self.half += 1
        self.runners = ['']*4
        if not parse.get_type(self.game[self.half][self.play_of_inn + 1])[0] == 's':
            self.defense = self.get_defense()

    def parse_plays(self):
        for half in self.game:
            parse.parse_half(self, half)

    def parse_debug(self, half, play):
        while self.half < half:
            parse.parse_half(self, self.game[self.half])
            print('parsing half ' + str(self.half))
        while self.inn_pbp_no <= play:
            parsed = parse.parse(self.game[self.half][self.inn_pbp_no], self)
            print('parsing play ' + str(self.inn_pbp_no))
        return parsed

    def parse_step(self):
        parsed = parse.parse(self.game[self.half][self.inn_pbp_no], self)
        print('parsing play ' + str(self.inn_pbp_no))
        return parsed


    def execute_play(self, p):
        self.last_play = p
        new_runners = ['']*4
        self.dest = ['']*4
        for e in reversed(p.events):
            if type(e) == play.RunEvent:
                for i in range(1, len(self.runners)):
                    if self.runners[i] != '':
                        runner = self.runners[i]
                        if runner.name == e.player:
                            self.dest[i] = e.dest[1] if e.dest[1] == 0 else e.dest[0]
            else:
                r = play.Runner(e.player, self)
                if e.code in ['E', 'INT']:
                    r.resp = ''
                self.runners[0] = r
                self.dest[0] = e.dest[1] if e.dest[1] == 0 else e.dest[0]
        for i in range(0, 4):
            if self.dest[i] != '':
                if self.dest[i] in [1,2,3]:
                    new_runners[self.dest[i]] = self.runners[i]
                elif self.dest[i] == 4:
                    self.score[self.half % 2] += 1
                elif self.dest[i] == 0:
                    self.event_outs += 1
            else:
                if self.runners[i] != '':
                    new_runners[i] = self.runners[i]

        self.output.append(self.get_output(p))

        if self.leadoff_fl == True:
            self.leadoff_fl = False
        self.runners = new_runners
        self.dest = ['']*4
        self.outs += self.event_outs
        self.event_outs = 0

        if p.type == 'b':
            if p.off_team == 'a':
                self.a_order = (self.a_order + 1) % 9
            else:
                self.h_order = (self.h_order + 1) % 9
        self.play += 1
        self.play_of_inn += 1
        print('play no: ' + str(self.play))

        self.sub = []

    def get_output(self, p):
        output = {'inning': round(self.half/2+.51),
        'half': self.half % 2,
        'outs': self.outs,
        'balls': self.count[0],
        'strikes': self.count[1],
        'seq': self.seq, # add x if in play
        'a_score': self.score[0],
        'h_score': self.score[1],
        'batter': p.batter,
        'batter_order': self.a_order if self.half % 2 == 0 else self.h_order, #
        'batter_pos': self.lineups.a_lineup.iloc[self.a_order]['pos'] if self.half % 2 == 0 else  self.lineups.h_lineup.iloc[self.h_order]['pos'], #
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
        'full_event': p.event[0], #
        'leadoff_fl': 1 if self.play_of_inn == 0 else 0,
        'event_text': p.events[0].det_abb,
        'event_cd': p.events[0].ev_code, #
        'bat_event_fl': 'T' if p.type == 'b' else 'F', #
        'sac_fl': 'T' if 'SAC' in p.text else 'F', #
        'event_outs': self.event_outs,
        'rbi': 1 if ', RBI' in p.text else int(p.text.split(' RBI')[0][-1]) if 'RBI' in p.text else 0,
        'fielder': '', #
        'batted_ball': '', #
        'errors': {}, #
        'h_fl': 'T' if p.events[0].ev_code in [20, 21, 22, 23] else 'F',
        'sb_fl': 'T' if 'stole' in p.text else 'F',
        'cs_fl': 'T' if 'caught stealing' in p.text else 'F',
        'pk_fl': 'T' if 'picked off' in p.text else 'F',
        'sub_fl': self.sub, # new, position, removed,
        'po': {}, #,
        'assist': {},
        'event_no': self.play+1, #
        'event_text': '',
        'pbp_text': p.text
        }
        return output

    def make_sub(self, s):
        self.lineups.make_sub(s, self)
        self.sub.append([s.sub_in, s.pos, s.sub_out])

    def get_defense(self):
        if self.half % 2 == 0:
            team = 'h'
        else:
            team = 'a'
        return self.lineups.get_defense(team)

    # def output(self):
    #     pass

def get_pbp(game_id) -> list:
    """
    extracts pbp text from table

    Parameters
    ----------
    game_id : int
        unique game id

    Returns
    -------
    list
        Play by play text as a list of lists,
        with each sublist containing play by play for a half inning
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
                if half %2 == 0:
                    if (i-2) % 3 == 0:
                        plays.append(e.text)
                        none = 0
    return game

def clean_plays(plays) -> list:
    new_plays = []
    for play in plays:
        if not 'No play.' in play:
            if 'fielder\'s choice' in play:
                fc = re.search(r"(out at first [a-z0-9]{1,2} to [a-z0-9]{1,2}, )reached on a fielder's choice", play)
                if not fc is None:
                    play = play.replace(fc.group(1), '')
            play = play.replace('did not advance', 'no advance')
            new_plays.append(play.replace('3a', ':').replace(';', ':').replace(': ', ':').replace('a muffed throw', 'an error'))
    return new_plays
