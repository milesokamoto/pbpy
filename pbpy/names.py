import Levenshtein
import re
import parse
import play
import pandas as pd

class NameDict:
    """docstring for NameDict."""

    def __init__(self, g):
        self.h_names = match_all(g, 'h')
        self.a_names = match_all(g, 'a')

    def match_name(self, team, name, type):
        max = 0
        match_team = team
        match = ''
        if team == "h":
            d1 = self.h_names
            d2 = self.a_names
        elif team == "a":
            d1 = self.a_names
            d2 = self.h_names
        for full, short in d1.items():
            if short == '':
                ratio = name_similarity(name, full)
                if ratio > max:
                    max = ratio
                    match = full
            elif short == name:
                max = 1
                match = full
        if type == 's':
            for full, short in d2.items():
                if short == '':
                    ratio = name_similarity(name, full)
                    if ratio > max:
                        max = ratio
                        match = full
                        match_team = 'a' if team == 'h' else 'h'
                elif short == name:
                    if max < .8:
                        max = 1
                        match = full
                        match_team = 'a' if team == 'h' else 'h'
        if not match == '':
            if match_team == team:
                d1[match] = name
                if match_team == "h":
                    self.h_names = d1
                elif match_team == "a":
                    self.a_names = d1
            else:
                d2[match] = name
                if match_team == "h":
                    self.h_names = d2
                elif match_team == "a":
                    self.a_names = d2
        return [match, match_team]

def match_all(g, team):
    starters = [p.name for p in g.lineups.a_lineup] if team == 'a' else [p.name for p in g.lineups.h_lineup]
    lu = starters[0:9]
    box_names = {s:'' for s in lu}
    pbp_names = []
    for h in range(0, len(g.game)):
        if team == 'a' and h % 2 == 0:
            for p in g.game[h]:
                if parse.get_type(p)[0] == 'p':
                    n = play.get_primary(p, play.get_event(p, "")[0])
                    if not n in pbp_names and not n is None:
                        pbp_names.append(n)
        elif team == 'h' and h % 2 == 1:
            for p in g.game[h]:
                if parse.get_type(p)[0] == 'p':
                    n = play.get_primary(p, play.get_event(p, "")[0])
                    if not n in pbp_names and not n is None:
                        pbp_names.append(n)
    nm = match_helper(box_names, pbp_names)
    def_plays = g.all_plays('a' if team == 'h' else 'h')
    pitcher_subs = [p for p in def_plays if (' to p.' in p and not 'out to p.' in p and not 'up to p.' in p and not '1b to p.' in p) or ' to p for ' in p]
    if len(starters) > 9:
        if ' for ' in pitcher_subs[0]:
            nm[starters[9]] = pitcher_subs[0][0:-1].split(' to p for ')[1]
        else:
            nm[starters[9]] = ''
    pitchers = [p.split(' to p')[0] for p in pitcher_subs]
    subs = g.lineups.a_sub if team == 'a' else g.lineups.h_sub
    plays = g.all_plays('')
    p_no = 0
    for sub in subs:
        if sub.pos in ('ph', 'pr'):
            nm[sub.name] = [re.match(r'(.*)(?: pinch (?:hit|ran) for )' + nm[sub.sub], s).group(1) for s in plays if ' pinch ' in s and nm[sub.sub] in s.split(' for ')[1]][0]
        elif sub.pos == 'p':
            nm[sub.name] = pitchers[p_no]
            p_no += 1
        else:
            nm[sub.name] = [re.match(r'(.*)(?: to ' + sub.pos + ' for )' + nm[sub.sub], s).group(1) for s in plays if ' to ' + sub.pos + ' for ' in s and nm[sub.sub] in s.split(' for ')[1]][0]
    blank = [k for k, v in sorted(nm.items(), key=lambda item: item[1]) if v == '']
    for name in blank:
        # print(name)
        # print([p.__dict__ for p in subs])
        sub_out = [[s.name, s.pos, s.sub] for s in subs if s.sub == name][0]
        sub_txt = [t for t in g.all_plays('') if nm[sub_out[0]] + ' to ' + sub_out[1] + ' for ' in t]
        if len(sub_txt) > 0:
            nm[sub_out[2]] = re.search(r'(?<=' + nm[sub_out[0]] + r' to ' + sub_out[1] + r' for ).*(?=\.)', sub_txt[0]).group()
    return nm


def match_helper(box_names, pbp_names):
    i=0
    for key in box_names.keys():
        if box_names[key] == '' and name_similarity(pbp_names[i], key) >= .5:
            box_names[key] = pbp_names[i]
        # elif len(box_names) == len(pbp_names) and name_similarity(box_names[len(box_names-1)], pbp_names[len(pbp_names-1)]) < .5:
            #Add in position not in the lineup and shift everyone else down (including subs order)
        i+=1
    # combos = []
    # for n1 in box_names.keys():
    #     for n2 in pbp_names:
    #         combos.append([n1, n2, name_similarity(n1,n2)])
    # matches = []
    # names_tbl = pd.DataFrame(combos, columns = ['pbp_name', 'box_name', 'sim'])
    # while len(names_tbl) > 0:
    #     max_index = names_tbl["sim"].idxmax()
    #     match = names_tbl.loc[max_index]
    #     names_tbl = names_tbl[names_tbl.pbp_name != match[0]]
    #     names_tbl = names_tbl[names_tbl.box_name != match[1]]
    #     box_names[match[0]] = match[1]
    return box_names

def get_name(s: str) -> str:
    """
    extracts name from start of play string
    Parameters
    ----------
    s : str
        play string
    """
    name = re.search(r"^[A-Za-z,\. '-]*?(?= [a-z])", s)
    if not name is None:
        return name.group()


def name_similarity(part, full):
    max_score = Levenshtein.ratio(part.title(), full.title())
    if part.title() in full.title():
        max_score = .5
    clean = full.replace(',', ' ').replace('-', ' ').replace('.', ' ').replace('  ', ' ')
    rev = clean.split(' ')
    rev.reverse()
    score = Levenshtein.ratio(part.title(), ' '.join(rev))
    if score > max_score:
        max_score = score
    if (len(full) - len(part)) > 5:
        score = Levenshtein.ratio(part.title(), full.title()[0:len(part)])
    if score > max_score:
        max_score = score
    return max_score
