class Player:
    def __init__(self, name, pos, switch, order, sub):
        self.name = name
        self.pos = pos
        self.switch = switch
        self.order = order
        self.sub = sub


class Batter(Player):
    def __init__(self):
        self.game_log = {}