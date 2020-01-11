import game
import play
class Output:
    def __init__(self, g, p):
        self.pitcher = g.defense[0]
        self.inning = round(g.half/2+.5)
        self.half = g.half % 2
        self.outs = g.outs
        self.balls = 0 #
        self.strikes = 0 #
        self.seq = '' #
        self.a_score = g.score[0]
        self.h_score = g.score[1]
        self.batter = p.batter
        self.batter_order = 0 #
        self.batter_pos = ''#
        self.batter_dest = g.dest[0]
        self.batter_play = ''
        [self.pitcher, self.pos_2, self.pos_3, self.pos_4,
            self.pos_5, self.pos_6, self.pos_7, self.pos_8, self.pos_9] = g.defense
        self.run_1 = g.runners[1].name if g.runners[1] != '' else ''
        self.run_1_resp = g.runners[1].resp if g.runners[1] != '' else ''
        self.run_1_dest = g.dest[1] if g.runners[1] != '' else ''
        self.run_1_play = ''
        self.run_2 = g.runners[2].name if g.runners[2] != '' else ''
        self.run_2_resp = g.runners[2].resp if g.runners[2] != '' else ''
        self.run_2_dest = g.dest[2] if g.runners[2] != '' else ''
        self.run_2_play = ''
        self.run_3 = g.runners[2].name if g.runners[3] != '' else ''
        self.run_3_resp = g.runners[2].resp if g.runners[3] != '' else ''
        self.run_3_dest = g.dest[2] if g.runners[3] != '' else ''
        self.run_play = ''
        self.full_event = '' #
        self.leadoff_fl = 1 if g.play == 0 else 0
        self.event_text = p.text
        self.event_cd = 0 #
        self.bat_event_fl = p.type#
        self.sac_fl = False #
        self.event_outs = 0 #
        self.rbi = 0 #
        self.fielder = '' #
        self.batted_ball = '' #
        self.errors = {} #
        self.sb_fl = {}
        self.cs_fl = {}
        self.pk_fl = {}
        self.sub_fl = {} # new, position, removed
        self.po = {} #
        self.assist = {}
        self.event_id = 0
        self.event_text = ''



class GameInfo:
    def __init__(self, g):
        self.game_id
