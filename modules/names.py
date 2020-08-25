import re

import Levenshtein
import pandas as pd

import modules.parse as parse
import modules.play as play
import modules.game as game
import modules.sub as sub


def match_all(lineup, play_list):
    """Create a dictionary matching the play by play names to box score names for a team

    :param lineup: object containing lineups and subs for a team
    :type lineup: Lineup object
    :param play_list: list of all pbp in the game
    :type play_list: list
    :return: dictionary of key box score name to value pbp name
    :rtype: dict
    """
    # make a dictionary with keys of the starters in the batting order and empty values
    starters = [p.name for p in lineup.lineup]
    lu = starters[0:9]
    box_names = {s:'' for s in lu}
    pbp_names = []
    sub_names = []

    # loop through play list to get a list of names used in play by play
    for h in range(0, len(play_list)):
        p_no = 0
        for p in play_list[h]:
            if (lineup.team == 0) ^ (h % 2 == 1):
                if parse.get_type(p) == 'p':
                    p_no += 1
                    n = p.split(' ' + play.find_events(p)[0])[0]
                    if not n in pbp_names and not n is None:
                        pbp_names.append(n)
                if p_no < 9 and parse.get_type(p) == 's':
                    ph_check = sub.parse_sub(p)
                    if ph_check[1] == 'ph':
                        n = ph_check[2]
                        if not n in pbp_names and not n is None:
                            pbp_names.append(n)
            if parse.get_type(p) == 's':
                sub_check = sub.parse_sub(p)
                if not sub_check[0] in sub_names and not sub_check[0] is None:
                    sub_names.append(sub_check[0])
                if not sub_check[0] is None and not sub_check[1] in sub_names:
                    sub_names.append(sub_check[1])
    nm = match_helper(box_names, pbp_names)

    # look at all defensive plays to match pitchers
    def_plays = game.all_plays(play_list, (lineup.team + 1) % 2)
    pitcher_subs = [p for p in def_plays if parse.get_type(p) == 's' and ' to p' in p or '/ for ' in p]
    if len(starters) > 9 and len(pitcher_subs) > 0:
        if ' for ' in pitcher_subs[0]:
            short = pitcher_subs[0][0:-1].split(' for ')[1]
            if name_similarity(short, starters[9]) >= .5:
                nm[starters[9]] = short
            else:
                nm[starters[9]] = ''                
        # if a position player moves to pitcher and burns the dh (syntax '/ for <name>), this will match the starter to his name
        elif len(pitcher_subs) > 1 and '/ for ' in pitcher_subs[1]:
            short = pitcher_subs[1][0:-1].split(' for ')[1]
            if name_similarity(short, starters[9]) >= .5:
                nm[starters[9]] = short
        else:
            nm[starters[9]] = ''
    else:
        unmatched = [s for s in nm.keys() if nm[s] == '']
        if len(unmatched) == 1:
            if ' for ' in pitcher_subs[0]:
                short = pitcher_subs[0][0:-1].split(' for ')[1]
            else:
                short = pitcher_subs[0].split(' to p')[0]
            if name_similarity(short, unmatched[0]) >= .5:
                nm[unmatched[0]] = short
    pitchers = [p.split(' to p')[0] for p in pitcher_subs if ' to p' in p]
    # matching subs
    subs = lineup.subs
    plays = game.all_plays(play_list, '')
    if not subs is None:
        pitcher_no = 0
        for i in range(len(subs)):
            s = subs[i]
            matched = False
            # offensive substitution
            if s.pos in ('ph', 'pr'):
                if not nm[s.sub] == '':
                    match = [re.match(r'(.*)(?: pinch (?:hit|ran) for )' + nm[s.sub] + r'\.', p).group(1) for p in plays if ' pinch ' in p and nm[s.sub] in p[-len(s.sub)-2:]]
                # if pbp text says pinch hit/pinch ran it's easy
                    if len(match) > 0:
                        nm[s.name] = match[0]
                        matched = True
                # otherwise it might say "to dh for"
                    else:
                        if (s.name in nm.keys() and nm[s.name] == '') or not s.name in nm.keys():
                            players = lineup.lineup
                            sub_match = [p.pos for p in players if p.name == s.sub]
                            ph_dh = False
                            if len(sub_match) > 0:
                                ph_dh = sub_match[0] == 'dh'
                            if s.pos == 'ph' and ph_dh:
                                match = [re.match(r'(.*)(?: to dh for )' + nm[s.sub] + r'\.', p).group(1) for p in plays if nm[s.sub] in p[-len(s.sub)-2:]]
                                if len(match) > 0:
                                    nm[s.name] = match[0]
                                    matched = True
                                else:
                                    nm[s.name] = ''
                            else:
                                nm[s.name] = ''
                else:
                    if not subs[-1] == s:
                        subs.append(s)
                        s = ''
                    else:
                        nm[s.name] = ''
            # pitcher substitution - assumes pitchers are listed in correct order
            elif s.pos == 'p':
                if pitcher_no < len(pitchers):
                    while pitchers[pitcher_no] in list(nm.values()) and pitcher_no < len(pitchers)-1:
                        pitcher_no += 1
                    if name_similarity(pitchers[pitcher_no], s.name) >= .5:
                        nm[s.name] = pitchers[pitcher_no]
                        matched = True
                        if s.order < 9:
                            pitcher_no = 0
                        else:
                            pitcher_no += 1
                    else:
                        while name_similarity(pitchers[pitcher_no], s.name) < .5 and pitcher_no < len(pitchers) - 1:
                            pitcher_no += 1
                        if name_similarity(pitchers[pitcher_no], s.name) >= .5:
                            nm[s.name] = pitchers[pitcher_no]
                            matched = True
                            pitcher_no = 0
                if not matched:
                    off_plays = game.all_plays(play_list, (lineup.team) % 2)
                    pitcher_subs2 = [p for p in off_plays if (' to p.' in p and not 'out to p.' in p and not 'up to p.' in p and not '1b to p.' in p) or ' to p for ' in p or '/ for ' in p]
                    pitchers2 = [p.split(' to p')[0] for p in pitcher_subs2 if ' to p' in p]
                    pitcher_no = 0
                    max_sim = .5
                    max_idx = None
                    while pitcher_no < len(pitchers2):
                        sim = name_similarity(pitchers2[pitcher_no], s.name)
                        if sim >= max_sim:
                            max_sim = sim
                            max_idx = pitcher_no
                        pitcher_no += 1
                    if not max_idx is None:
                        nm[s.name] = pitchers2[max_idx]
                        matched = True
                    pitcher_no = 0

            # all other subs
            else:
                match = [re.match(r'(.*)(?: to ' + s.pos + ' for )' + nm[s.sub], p).group(1) for p in plays if ' to ' + s.pos + ' for ' in p and nm[s.sub] in p.split(' for ')[1]]
                if len(match) > 0:
                    nm[s.name] = match[0]
                else:
                    nm[s.name] = ''
    if '' in subs:
        subs.remove('')


    #check if similarity score is less than .5 for any pair
    check = [k for k, v in sorted(nm.items(), key=lambda item: item[1]) if name_similarity(v, k) < .5]
    for i in range(0, len(check)):
        for j in range(i, len(check)):
            if name_similarity(check[i], nm[check[j]]) > name_similarity(check[i], nm[check[i]]) + .1:
                if name_similarity(check[j], nm[check[i]]) > name_similarity(check[i], nm[check[i]]) + .1:
                    temp = nm[check[i]]
                    nm[check[i]] = nm[check[j]]
                    nm[check[j]] = temp

    # check if any names are left blank
    blank = [k for k, v in sorted(nm.items(), key=lambda item: item[1]) if v == '']
    pbp_blank = [n for n in pbp_names if not n in nm.values()]
    subs_blank = [n for n in sub_names if not n in nm.values()]
    for name in blank:
        for n in pbp_blank:
            if name_similarity(n, name) >= .5:
                nm[name] = n

        if nm[name] == '':
            sub_out = [[s.name, s.pos, s.sub] for s in subs if s.sub == name]
            if len(sub_out) > 0:
                if sub_out[0][1] == 'pr':
                    sub_type = ' pinch ran'
                elif sub_out[0][1] == 'ph':
                    sub_type = ' pinch hit'
                else:
                    sub_type = ' to ' + sub_out[0][1]
                sub_txt = [t for t in plays if nm[sub_out[0][0]] + sub_type + ' for ' in t]
                if len(sub_txt) > 0:
                    nm[sub_out[0][2]] = re.search(r'(?<=' + nm[sub_out[0][0]] + sub_type + r' for ).*(?=\.)', sub_txt[0]).group()
                elif sub_out[0][1] == 'p':
                    sub_txt = [t for t in game.all_plays(play_list, '') if '/ for ' in t]
                    short = re.search(r'(?<=/ for ).*(?=\.)', sub_txt[0]).group()
                    if name_similarity(short, sub_out[0][2]) >= .5:
                        nm[sub_out[0][2]] = short
            else:
                sub_in = [[s.name, s.pos, s.sub] for s in subs if s.name == name]
                if len(sub_in) > 0:
                    if sub_in[0][1] == 'pr':
                        sub_type = ' pinch ran'
                    elif sub_in[0][1] == 'ph':
                        sub_type = ' pinch hit'
                    else:
                        sub_type = ' to ' + sub_in[0][1]
                    if len(sub_in) > 0:
                        sub_txt = [t for t in game.all_plays(play_list, '') if sub_type + ' for ' + nm[sub_in[0][2]] in t]
                        if len(sub_txt) > 0:
                            nm[sub_in[0][0]] = re.search(r'.*(?=' + sub_type + r' for ' + nm[sub_in[0][2]] + r'\.)', sub_txt[0]).group()
                        else:
                            sub_txt = [t for t in game.all_plays(play_list, '') if sub_type + ' for ' in t]
                            if len(sub_txt) == 1:
                                nm[sub_in[0][0]] = re.search(r'.*(?=' + sub_type + r' for )', sub_txt[0]).group()

        if nm[name] == '':
            for n in subs_blank:
                if name_similarity(n, name) >= .7:
                    nm[name] = n

    for player in lineup.lineup:
        if player.name in nm.keys():
            player.pbp_name = nm[player.name]
        else:
            player.pbp_name = player.name
    for player in lineup.subs:
        player.pbp_name = nm[player.name]
    
    return lineup
    
def match_helper(box_names, pbp_names):
    """matches names from box score to names in the pbp score and returns completed dictionary

    :param box_names: dictionary with keys of names from box score and empty values
    :type box_names: dict
    :param pbp_names: list of names in order of appearance in play-by-play
    :type pbp_names: list
    :return: dictionary with keys of names from box score and values of matching names from pbp
    :rtype: dict
    """
    #TODO: check threshold value and find false positives
    i=0
    for key in box_names.keys():
        if box_names[key] == '' and name_similarity(pbp_names[i], key) >= .5:
            box_names[key] = pbp_names[i]
            i+=1
        else:
            if i < len(box_names.keys())-1:
                if box_names[key] == '' and name_similarity(pbp_names[i+1], key) >= .5:
                    box_names[key] = pbp_names[i+1]
                    i += 2
    return box_names

def strip_non_alpha(str):
    return str.replace('.', '').replace(',', ' ').replace("'", '').replace('-', ' ')

def bigram(str):
    seq = []
    for i in range(0, len(str)-1):
        seq.append(str[i:i+2])
    return(seq)

def name_similarity(part, full):
    p = strip_non_alpha(part).title()
    f = full

    first = strip_non_alpha(f.split(', ')[-1]).title()
    last = strip_non_alpha(f.split(', ')[0]).title()

    if first in p and last in p:
        return 1
    
    if last in p and first[0] in p.replace(last, ''):
        return .9

    if last in p:
        return .8

    if ' ' in last:
        if last.split(' ')[0] in p or last.split(' ')[1] in p:
            print(last.split(' '))
            print(p)
            return .7
    
    if '-' in full:
        if last.split(' ')[0][0] + '.' + '-' + last.split(' ')[1][0] + '.' in part:
            return .5

    max_score = 0

    if '. ' in part:
        if first[0] + '. ' + last[0:len(part)-3] == part:
            max_score = .5
    
    if ' ' in p:
        bi1 = bigram(last)
        for pt in p.split(' '):
            bi2 = bigram(pt)
            score = compare_bi(bi1, bi2)
            if score > max_score:
                max_score = score
            if one_transpose(pt, last):
                if .6 > max_score:
                    max_score = .6

    bi2 = bigram(p)
    for nm in [last, first]:
        bi1 = bigram(nm)
        score = compare_bi(bi1, bi2)
        if score > max_score:
            max_score = score

    if one_transpose(p, last):
        if .6 > max_score:
            max_score = .6

    print(part + ' VS ' + full + ':' + str(max_score))
    return(max_score)

def compare_bi(bi1, bi2):  
    union = len(bi1) + len(bi2)

    if union == 0 or union is None:
        return 0

    hit_count = 0
    for x in bi1:
        for y in bi2:
            if x == y:
                hit_count += 1
                break
    return((2.0 * hit_count) / union)

def one_transpose(str1, str2):
    for i in range(2, len(str1)):
        check = str1[0:i-1] + str1[i] + str1[i-1] + str1[i+1:]
        if check == str2:
            return True
    return False
