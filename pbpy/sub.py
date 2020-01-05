import re

class Sub:
    def __init__(self, text):
        self.team = get_sub_team(text)
        [self.in, self.pos, self.out] = parse_sub(text)

    def match_sub_names(self, names):
        self.in = names.match_name(self.team, self.in)
        if not self.out is None:
            self.out = names.match_name(self.team, self.out)

def parse_sub(s):
    s = s.replace('/ ', '/ to x')
    sub = re.search(r"^([A-Za-z,\. '-]*?(?= [a-z])|\/) (pinch (?:hit|ran)|to [0-9a-z]{1,2})* *(?:for ([A-Za-z,\. '-]*?)\.$)*", s)
    if not sub is None:
        sub = [sub.group(1), sub.group(2), sub.group(3)]
        if not sub[1] is None:
            if 'hit' in s:
                sub[1] = 'ph'
            elif 'ran' in s:
                sub[1] = 'pr'
            else:
                sub[1] = (re.search(r'(?<=to )[0-9a-z]{1,2}', sub[1]).group())
            return sub
    raise TypeError('No sub')

def get_sub_type(s):
    if 'pinch' in s[1]:
        subtype = 'OFF'
        # if s[2] is None:
        #     [order]
    elif 'to dh' in s[1]:
        if 'for' in s:
            subtype = 'OFF'
        else:
            subtype = 'DEF'
    else:
        subtype = 'DEF'
