import re
import play
import sub

def parse_half(half):
    for play in half:
        print(parse(play))

def parse(s):
    [type, text] = get_type(s)
    if type == 's':
        sub = sub.Sub(text)
    elif type == 'p'
        play = play.Play(text)

def get_type(s): #  PLAY OR SUB -> BREAK DOWN INTO PARTS
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
            return ['s', subtest]
    return ['p', s.split(':')]


half = ['McKENZIE reached on an error by 2b (3-2).', 'JANSEN grounded into double play 1b to ss to p (0-1): McKENZIE out on the play.', 'NISLE singled up the middle (0-1).', 'FASCIA flied out to lf (3-2).']
parse_half(half)
