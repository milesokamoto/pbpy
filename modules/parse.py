import re

import modules.play as play
import modules.sub as sub

def parse_half(g, half):
    for play in half:
        if check_play(play, g):
            parse(play, g)
        else:
            g.inn_pbp_no += 1
    if g.half < len(g.game)-1:
        g.advance_half()

def parse(pbp_txt, g):
    if len(g.output) >= 4:
        if g.output[-1]['bat_event_fl'] == 0 and g.output[-2]['bat_event_fl'] == 0 and g.output[-3]['bat_event_fl'] == 0 and g.output[-4]['bat_event_fl'] == 0:
            g.error = True
    play_type = get_type(pbp_txt)
    if play_type == 's':
        s = sub.Sub(pbp_txt, g)
        g.make_sub(s)
        if len(g.game[g.half]) > g.inn_pbp_no:
            if not get_type(g.game[g.half][g.inn_pbp_no]) == 's':
                g.defense = g.get_defense()
    elif play_type == 'p':
        # try:
        p = play.Play(pbp_txt, g)
        g.execute_play(p)
        # except:
        #     input('ERROR: ' + pbp_txt + ' game: ' + str(g.id))
        #     return None
    g.pbp_no += 1
    g.inn_pbp_no += 1
    if type == 's':
        return s
    elif type == 'p':
        return p

def check_play(pbp_text, g):
    pbp_text = pbp_text.replace('/ ', '/ to x')
    subtest = re.search(r"^([A-Za-z,\. '-]*?(?= [a-z])|\/) (pinch (?:hit|ran)|to [0-9a-z]{1,2})* *(?:for ([A-Za-z,\. '-]*?)\.$)*", pbp_text)
    if subtest is None:
        if not play.get_event(pbp_text, '') == "None":
            return False
    if ' pinch hit' in pbp_text and not 'for' in pbp_text:
        return False
    return True


def get_type(s):
    """given a play by play string, determine if it's a play or substitution

    :param s: play by play text
    :type s: str
    :return: 's' for substitution or 'p' for play
    :rtype: str
    """
    expr = r"^([A-Za-z,\. '-]*?(?= [a-z])|\/) (pinch (?:hit|ran)|to [0-9a-z]{1,2})* *(?:for ([A-Za-z,\. '-]*?)\.$)*"
    search = re.search(expr, s.replace('/ ', '/ to x'))
    if not search is None:
        if not search.group(2) is None:
            return 's'
        else:
            return 'p'
    else:
        return 'n'