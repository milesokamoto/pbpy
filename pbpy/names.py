import Levenshtein
import re

class NameDict:
    """docstring for NameDict."""

    def __init__(self, lineups):
        self.h_names = {name: '' for name in lineups.all_names('h')}
        self.a_names = {name: '' for name in lineups.all_names('a')}

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
                    if max < 1:
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
    part = part.title()
    max_score = Levenshtein.ratio(part, full)
    clean = full.replace(',', ' ').replace('-', ' ').replace('.', ' ').replace('  ', ' ')
    rev = clean.split(' ')
    rev.reverse()
    score = Levenshtein.ratio(part, ' '.join(rev))
    if score > max_score:
        max_score = score
    return max_score
