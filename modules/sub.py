import re
import modules.names as names

class Sub:
    def __init__(self, team, player, text):
        """Base class sub

        :param team: 'h' for home or 'a' for away
        :type team: str
        :param player: player's id
        :type player: [type]
        :param text: [description]
        :type text: [type]
        """        
        self.team = team
        self.player = player
        self.text = text

class PositionSwitch(Sub):
    def __init__(self, team, player, pos, text):
        super().__init__(team, player, text)
        self.pos = pos

class DefensiveSub(Sub):
    def __init__(self, team, player, sub, pos, text):
        super().__init__(team, player, text)
        self.sub = sub
        self.pos = pos

class OffensiveSub(Sub):
    def __init__(self, team, player, sub, sub_type, text):
        super().__init__(team, player, text)
        self.sub = sub
        self.sub_type = sub_type

class Removal(Sub):
        def __init__(self, team, sub, text):
            self.team = team
            self.sub = sub
            self.text = text

def rev_dict(value, dict):
    val = [k for k, v in sorted(dict.items(), key=lambda item: item[1]) if v == value]
    if not val == []:
        return val[0]
    else:
        return -1

def parse_sub(s):
    s = s.replace('/ ', '/ to x ')
    sub = re.search(r"^([A-Za-z,\. '-]*?(?= [a-z])|\/) (pinch (?:hit|ran)|to [0-9a-z]{1,2})* *(?:for ([A-Za-z,\. '-]*?)\.$)*", s)
    if not sub is None:
        sub = [sub.group(1), sub.group(2), sub.group(3)]
        if not sub[1] is None:
            if ' hit ' in s:
                sub[1] = 'ph'
            elif ' ran ' in s:
                sub[1] = 'pr'
            else:
                sub[1] = (re.search(r'(?<=to )[0-9a-z]{1,2}', sub[1]).group())
            return sub
    raise TypeError('Not a substitution')

def get_sub_type(s):
    if 'pinch' in s:
        return 'o'
        # if s[2] is None:
        #     [order]
    else:
        return 'd'

def get_sub_team(half, type):
    if half %2 == 0:
        if type == 'o':
            return 'a'
        else:
            return 'h'
    else:
        if type == 'o':
            return 'h'
        else:
            return 'a'
