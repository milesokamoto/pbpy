class Player:
    def __init__(self, name, pos, switch, order, sub):
        self.name = name
        self.pos = pos
        self.switch = switch
        self.order = order
        self.sub = sub
        self.status = 'available'
        self.play_text = []


class Batter(Player):
    def __init__(self):
        self.game_log = {}


class Pitcher(Player):
    def __init__(self):
        self.game_log = {}