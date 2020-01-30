import re
import play
import sub

def parse_half(g, half):
    for play in half:
        parse(play, g)
    if g.half < len(g.game)-1:
        g.advance_half()

def parse(pbp_txt, g):
    if len(g.output) >= 3:
        if g.output[-1]['bat_event_fl'] == 0 and g.output[-2]['bat_event_fl'] == 0 and g.output[-3]['bat_event_fl'] == 0:
            print("ERROR HERE")
            g.error = True
    [type, txt] = get_type(pbp_txt)
    if type == 's':
        s = sub.Sub(pbp_txt, g)
        g.make_sub(s)
        if len(g.game[g.half]) > g.play_of_inn + 1:
            if not get_type(g.game[g.half][g.play_of_inn + 1])[0] == 's':
                g.defense = g.get_defense()
    elif type == 'p':
        try:
            p = play.Play(pbp_txt, g)
            g.execute_play(p)
        except:
            input('ERROR: ' + pbp_txt)
            return None
    g.pbp_no += 1
    g.inn_pbp_no += 1
    if type == 's':
        return s
    elif type == 'p':
        return p

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
