import Levenshtein
import re

class NameDict:
    """docstring for NameDict."""

    def __init__(self, lineups):
        self.h_names = {name: '' for name in lineups.all_names('h')}
        self.a_names = {name: '' for name in lineups.all_names('a')}

    def match_name(self, team, name):
        max = 0
        if team == "h":
            d = self.h_names
        elif team == "a":
            d = self.a_names
        else:
            raise
        for full, short in d.items():
            if short != name:
                ratio = Levenshtein.ratio(name, full)
                if ratio > max:
                    max = ratio
                    match = full
            else:
                max = 1
                match = full
        d[match] = name
        if team == "h":
            self.h_names = d
        elif team == "a":
            self.a_names = d
        return match



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
