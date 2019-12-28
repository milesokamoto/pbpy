import dict
import names
import re


def parse(text):
    [event, code] = get_event(text)
    primary = get_primary(text, event)
    return [primary, code]


def get_event(text):
    return [[key, dict.codes[key]] for key in dict.codes.keys() if key in text][0]


def get_loc(text):
    return [dict.loc_codes[key] for key in dict.loc_codes.keys() if key in text][0]


def get_primary(text, event):
    return text.split(' ' + event)[0]


def get_run(text):
    return [[key, dict.run_codes[key]] for key in dict.run_codes.keys() if key in text][0]


def get_fielders(text, event):
    return [dict.pos_codes[key] for key in dict.pos_codes.keys() if key in text.split(' ' + event)[1]]

def get_type(text):
    """
    checks whether play is a substitution, returns list
    containing name of player substituted in, sub type/position,
    and player substituted out if applicable
    Parameters
    ----------
    s : str
        pbp string

    Returns
    -------
    list
        substitution summary: [sub in, sub type/position,
        sub out or None]
    bool
        false if there is no substitution
    """
    s = s.replace('/ ', '/ to x')
    subtest = re.search(r"^([A-Za-z,\. '-]*?(?= [a-z])|\/) (pinch (?:hit|ran)|to [0-9a-z]{1,2})* *(?:for ([A-Za-z,\. '-]*?)\.$)*", s)
    if not subtest is None:
        subtest = [subtest.group(1), subtest.group(2), subtest.group(3)]
        if not subtest[1] is None:
            return subtest
        return False
