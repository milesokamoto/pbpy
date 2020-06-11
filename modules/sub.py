import re
import modules.names as names

class Sub:
    def __init__(self, text, game):
        self.team = get_sub_team(game.half, get_sub_type(text))
        [self.sub_in_short, self.pos, self.sub_out_short] = parse_sub(text)
        self.match_sub_names(game.names)

    def match_sub_names(self, names):
        n = names.h_names if self.team == 'h' else names.a_names
        if '/' in self.sub_in_short:
            self.sub_in = '/'
        else:
            self.sub_in = rev_dict(self.sub_in_short, n)
        if not self.sub_out_short is None:
            self.sub_out = rev_dict(self.sub_out_short, n)
        else:
            self.sub_out = None
        if self.sub_in == -1 or self.sub_out == -1:
            self.team = 'a' if self.team == 'h' else 'h'
            n = names.h_names if self.team == 'h' else names.a_names
            self.sub_in = rev_dict(self.sub_in_short, n)
            if not self.sub_out_short is None:
                self.sub_out = rev_dict(self.sub_out_short, n)
        # match = names.match_name(self.team, self.sub_in, 's')
        # if match[1] != self.team:
        #     self.team = match[1]
        # self.sub_in = names.match_name(self.team, self.sub_in, 's')[0]
        # if not self.sub_out is None:
            # self.sub_out = names.match_name(self.team, self.sub_out, 's')[0]

def rev_dict(value, dict):
    val = [k for k, v in sorted(dict.items(), key=lambda item: item[1]) if v == value]
    if not val == []:
        return val[0]
    else:
        return -1

def parse_sub(s):
    s = s.replace('/ ', '/ to x')
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
    raise TypeError('No sub')

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
