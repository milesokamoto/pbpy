import re

import Levenshtein
import pandas as pd

import modules.parse as parse
import modules.play as play
import modules.game as game


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

    # loop through play list to get a list of names used in play by play
    for h in range(0, len(play_list)):
        if (lineup.team == 0) ^ (h % 2 == 1):
            for p in play_list[h]:
                if parse.get_type(p) == 'p':
                    n = p.split(' ' + play.find_events(p)[0])[0]
                    if not n in pbp_names and not n is None:
                        pbp_names.append(n)
    nm = match_helper(box_names, pbp_names)

    # look at all defensive plays to match pitchers
    def_plays = game.all_plays(play_list, (lineup.team + 1) % 2)
    pitcher_subs = [p for p in def_plays if (' to p.' in p and not 'out to p.' in p and not 'up to p.' in p and not '1b to p.' in p) or ' to p for ' in p or '/ for ' in p]
    if len(starters) > 9 and len(pitcher_subs) > 0:
        if ' for ' in pitcher_subs[0]:
            nm[starters[9]] = pitcher_subs[0][0:-1].split(' for ')[1]
        # if a position player moves to pitcher and burns the dh (syntax '/ for <name>), this will match the starter to his name
        elif len(pitcher_subs) > 1 and '/ for ' in pitcher_subs[1]:
            short = pitcher_subs[1][0:-1].split(' for ')[1]
            if name_similarity(short, starters[9]) > .5:
                nm[starters[9]] = short
        else:
            nm[starters[9]] = '' # this might be a problem if we get to here
    pitchers = [p.split(' to p')[0] for p in pitcher_subs if ' to p' in p]\
    # matching subs
    subs = lineup.subs

    plays = game.all_plays(play_list, '')
    p_no = 0
    if not subs is None:
        for sub in subs:
            # offensive substitution
            if sub.pos in ('ph', 'pr'):
                match = [re.match(r'(.*)(?: pinch (?:hit|ran) for )' + nm[sub.sub] + r'\.', s).group(1) for s in plays if ' pinch ' in s and nm[sub.sub] in s[-len(sub.sub)-2:]]
                # if pbp text says pinch hit/pinch ran it's easy
                if len(match) > 0:
                    nm[sub.name] = match[0]
                
                # otherwise it might say "to dh for"
                else:
                    if (sub.name in nm.keys() and nm[sub.name] == '') or not sub.name in nm.keys():
                        players = lineup.lineup
                        sub_match = [p.pos for p in players if p.name == sub.sub]
                        ph_dh = False
                        if len(sub_match) > 0:
                            ph_dh = sub_match[0] == 'dh'
                        if sub.pos == 'ph' and ph_dh:
                            match = [re.match(r'(.*)(?: to dh for )' + nm[sub.sub] + r'\.', s).group(1) for s in plays if nm[sub.sub] in s[-len(sub.sub)-2:]]
                            if len(match) > 0:
                                nm[sub.name] = match[0]
                            else:
                                nm[sub.name] = ''
                        else:
                            nm[sub.name] = ''
            
            # pitcher substitution - assumes pitchers are listed in correct order
            elif sub.pos == 'p':
                while pitchers[p_no] in list(nm.values()) and p_no < len(pitchers):
                    p_no += 1
                if name_similarity(pitchers[p_no], sub.name) >= .5:
                    nm[sub.name] = pitchers[p_no]
                    if sub.order < 9:
                        p_no = 0
                    else:
                        p_no += 1
                else:
                    while name_similarity(pitchers[p_no], sub.name) < .5 and p_no < len(pitchers) - 1:
                        p_no += 1
                    if name_similarity(pitchers[p_no], sub.name) >= .5:
                        nm[sub.name] = pitchers[p_no]
                        p_no = 0

            # all other subs
            else:
                match = [re.match(r'(.*)(?: to ' + sub.pos + ' for )' + nm[sub.sub], s).group(1) for s in plays if ' to ' + sub.pos + ' for ' in s and nm[sub.sub] in s.split(' for ')[1]]
                if len(match) > 0:
                    nm[sub.name] = match[0]
                else:
                    nm[sub.name] = ''

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
    for name in blank:
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
                if name_similarity(short, sub_out[0][2]) > .5:
                    nm[sub_out[0][2]] = short
        else:
            sub_in = [[s.name, s.pos, s.sub] for s in subs if s.name == name]
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
    return box_names

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


