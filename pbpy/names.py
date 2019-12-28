import Levenshtein
import re
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

def match_name(df, name):
    max = 0
    for full, short in dict.items():
        if short != name:
            ratio = Levenshtein.ratio(name, full)
            if ratio > max:
                max = ratio
                match = full
        else:
            max = 1
            match = full
    dict[match] = name
    return [dict, full]
