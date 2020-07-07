class Player:
    def __init__(self, name, pos, switch, order, sub, status, team):
        self.name = name
        self.pos = pos
        self.switch = switch
        self.order = order
        self.sub = sub
        self.status = status # 'available', 'entered', 'removed'
        self.team = team
        self.pbp_name = None

    def match_pbp_name(self, names):
        nm = names.a_names if self.team == 0 else names.h_names
        self.pbp_name = nm[self.name]