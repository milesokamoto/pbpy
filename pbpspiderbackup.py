# -*- coding: utf-8 -*-
"""
Created on Fri Jul 4 9:30:10 2019

@author: Miles Okamoto

@todo:
-fix reset play to start over with custom input
-change runners[] if a pinch runner
-eventually index stats.ncaa pbp names to roster names to player ids

"""
import scrapy
from scrapy_splash import SplashRequest
import pandas as pd
from datetime import timedelta, date #build in script that runs everyday for yesterday
import re

teamindex = pd.read_csv('https://raw.githubusercontent.com/milesok/pbpy/master/teams.csv')
codes = {
    'singled': '1B',
    'doubled': '2B',
    'tripled': '3B',
    'homered': 'HR',
    'flied out': 'F',
    'flied into double play': 'F',
    'popped up': 'P',
    'infield fly': 'P', #label w/ flag?
    'popped into double play': 'F',
    'lined into double play': 'L',
    'lined out': 'L',
    'grounded out': 'G',
    'out at first': 'G', ##ONLY FOR BATTERS - check on this for fielding
    'grounded into double play': 'G',
    'hit into double play': 'G',
    'fouled into double play': 'F',
    'fouled out': 'F', #when doing fielders, add f after fielder code
    'struck out looking': 'KL',
    'struck out swinging': 'KS',
    'struck out': 'K',
    'hit by pitch': 'HBP',
    'walked': 'BB',
    'stole': 'SB',
    'picked off': 'PO',
    'caught stealing': 'CS',
    'wild pitch': 'WP',
    'passed ball': 'PB',
    'balk': 'BK',
    'batter\'s interference': 'BINT',
    'catcher\'s interference': 'C',
    'error': 'E',
    'fielder\'s choice': 'FC'
}
event_codes = {
    'G': 2,
    'F': 2,
    'P': 2,
    'L': 2,
    'BINT': 2,
    'KL': 3,
    'KS': 3,
    'K': 3,
    'SB': 4,
    'DI': 5,
    'CS': 6,
    'PO': 8,
    'WP': 9,
    'PB': 10,
    'BK': 11,
    'BB': 14,
    'IBB': 15,
    'HBP':16,
    'C': 17,
    'E': 18,
    'FC': 19,
    '1B': 20,
    '2B': 21,
    '3B': 22,
    'HR': 23
}
fielder_codes = {
    'P' : 1,
    'C' : 2,
    '1B' : 3,
    '2B' : 4,
    '3B' : 5,
    'SS' : 6,
    'LF' : 7,
    'CF' : 8,
    'RF' : 9,
    'DH' : 10,
    'PH' : 11
}
base_codes = {
    'first': 1,
    'second': 2,
    'third': 3,
    'home': 4,
    'scored': 4,
    'out': 0
}
loc_codes = {
    'to pitcher': 1,
    'to catcher': 2,
    'to first base': 3,
    'through the right side': 34,
    'to second base': 4,
    'to third base': 5,
    'through the left side': 56,
    'to shortstop': 6,
    'to left field': 7,
    'down the lf line': 7,
    'to left center': 78,
    'to center field': 8,
    'up the middle': 46,
    'to right center': 89,
    'to right': 9,
    'down the rf line': 9
}

def scrape_lineups(team: str, response) -> list:
    """
    Parameters
    ----------
    team : str
        'home' or 'away'
    response :
        webpage response

    Returns
    -------
    list
        [df containing lineup, list containing substitute names]
    """

    end = False
    lineup = []
    subs = []
    i = 1
    order = 1
    if team == 'away':
        j = 2
    else:
        j = 3
    while not end:
        pitcher = ''
        testname = response.xpath("//table[@class='mytable']["+str(j)+"]/tbody/tr[@class='smtext'][" + str(i) + "]/td[1]/a/text()").get()
        if testname is None: #would happen if it's not a link
            testname = response.xpath("//table[@class='mytable']["+str(j)+"]/tbody/tr[@class='smtext'][" + str(i) + "]/td[1]/text()").get()
        if not testname is None and not testname == 'Totals' :
            testname = testname.replace('\xa0', ' ') #replaces spaces in name field
            #for starting players
            if not "     " in testname: #filters out subs
                name = testname.replace('\n', '') #remove temp line character
                pos = response.xpath("//table[@class='mytable']["+str(j)+"]/tbody/tr[@class='smtext'][" + str(i) + "]/td[2]/text()").get()
                if not pos is None:
                    pos = pos.split('/')[0]
                if pos == "DH":
                    lineup.append([order, name, pos])
                    order += 1
                elif pos == "P":
                    if order <= 9: #check if pitcher is hitting
                        lineup.append([order, name, pos])
                        order += 1
                    else:
                        order = 'P'
                        lineup.append([order, name, pos])
                        end = True
                    pitcher = name
                else:
                    lineup.append([order, name, pos])
                    if order >= 9 and pitcher != '':
                        end = True
                    if order > 9:
                        end = True
                    order += 1
                i += 1
                #subs
            else:
                name = testname.replace('\n', '').replace('     ', '').replace(' ,', ',')
                i += 1
                subs.append(name)
        else:
            end = True
    return [pd.DataFrame(lineup, columns = ['order', 'name', 'position']), subs] #done

def get_pbp(response, inn_half: int, inn: int, line: int) -> list:
    """
    extracts pbp text from appropriate part of page

    Parameters
    ----------
    response : response
        webpage response from scraper
    inn_half : int
        0: top half of inning
        1: bottom half of inning
    inn : int
        inning ##could this be a list w/ inn_half
    line : int
        counter for line to extract text

    Returns
    -------
    str
        Play by play text
    """
    if inn_half == 0:
        play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][1]/text()").get()
        if not play is None:
            if 'No play' in play or 'Review' in play or 'review' in play or ('failed pickoff attempt.' in play and not 'advanced' in play):
                line += 1
                return get_pbp(response, inn_half, inn, line)
        else:
            play = "No Play"

    elif inn_half == 1: #right side for bottom half
        play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][3]/text()").get()
        if not play is None:
            if 'No play' in play or 'Review' in play or 'review' in play or ('failed pickoff attempt.' in play and not 'advanced' in play):
                line += 1
                return get_pbp(response, inn_half, inn, line)
        else:
            play = "No Play"
    if play == 'No Play':
        end = True
    else:
        end = False
    play = play.replace('3a', ':').replace(';', ':').replace('a dropped fly', 'an error').replace('a muffed throw', 'an error') #replace with input if both out at first and fielders choice
    if 'out at first' in play and 'fielder\'s choice' in play:
        play = input('play: ' + play + '\nEnter corrected play text: ')
    return [play, line, end] #done

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
    else:
        input = input('play: ' + s + '\nEnter player name: ') #done
        if input == 'skip':
            return None
        else:
            return input

def parse_name(name: str) -> str:
    """
    reformats name
    Parameters
    ----------
    name : str
        name extracted from pbp text
    """
    if name is None:
        return None
    if '.' in name:
        if name.split('.')[1] == '':
            name = name.replace('.', '')
        elif 'St.' in name:
            name = name + ','
        else:
            name = name.replace('. ', ' ')
            name = name.replace('.', ' ')
    if ' ' in name and not ',' in name:
        if not len(name.split(' ')[0]) == 1 and not len(name.split(' ')[1]) > 3:
            name = name.replace(' ', ', ')
    if ',' in name and not ', ' in name:
        name = name.replace(',', ', ')
    if 'De La ' in name or 'van ' in name or 'Van ' in name or 'De Seda' in name and not ',' in name:
        name = name + ','
    if ' ' in name and not ',' in name:
        name_temp =  ', ' + name.split(' ')[0]
        for m in range(1, len(name.split(' '))):
            name_temp = name.split(' ')[len(name.split(' '))-m] + ' ' + name_temp
        name_temp = name_temp.replace(' , ', ', ')
        name = name_temp
    if not ',' in name:
        name = name + ','
    return name

def get_sub_lists(lineups: list, subtype: str, inn_half) -> list:
    """
    returns corresponding team lineup and substitutions

    Parameters
    ----------
    lineups : list
        a list containing home and away lineups and subs:
        [home_lineup, home_subs, store_hm_order,
        away_lineup, away_subs, store_aw_order]
    subtype : str
        'OFF' or 'DEF'

    Returns
    -------
    list
        3 elements: [dataframe of lineup (order, name, position), substitution list, which team's lineups]
    """
    if subtype == 'OFF':
        if inn_half == 0:
            lu = lineups[3]
            subs = lineups[4]
            team = 'away'
        else:
            lu = lineups[0]
            subs = lineups[1]
            team = 'home'
    else:
        if inn_half == 0:
            lu = lineups[0]
            subs = lineups[1]
            team = 'home'
        else:
            lu = lineups[3]
            subs = lineups[4]
            team = 'away'
    return [lu, subs, team]

def get_pos(s: str) -> str:
    """
    extracts position from substitution text
    Parameters
    ----------
    s : str
        string containing substitution text
    """
    if 'hit' in s:
        return 'PH'
    elif 'ran' in s:
        return 'PR'
    else:
        return (re.search(r'(?<=to )[0-9a-z]{1,2}', s).group()).upper()

def find_name(name: str, list: list) -> str:
    """
    finds player's full name in given list and return as string

    Parameters
    ----------
    name : str
        name from pbp text
    list : list
        list of names to match
    Returns
    -------
    str
        full name of player as found in box score
    """
    full = next((s for s in list if name.lower() in s.lower()), None)
    if full is None:
        full = input('name: ' + name + '\nlist: ' + str(list) + '\nInput name of player: ') ##implement "reset play"
    return full

def make_sub(s: list, lineups: list, inn_half: int, runners) -> list:
    """
    takes list representing substitution and changes lineup to reflect changes

    Parameters
    ----------
    s : list
        list of strings: [sub in, position, sub out]
    lu : df
        dataframe containing team's lineup with cols 'order', 'name', 'position'
    subs : list
        list containing full names of all non-starters from box score

    Returns
    -------
    list
        new lineups

    """

    if 'pinch' in s[1]:
        subtype = 'OFF'
    elif 'to dh' in s[1]:
        subtype = input(lineups[0] + lineups[3] + '\n OFF or DEF? ')
    else:
        subtype = 'DEF'

    [lu, subs, team] = get_sub_lists(lineups, subtype, inn_half)
    if '/' in s[0]:
        s[0] = lu[lu['position']=='P'].iloc[0]['name']
        s[1] = ' to p'
    pos = get_pos(s[1])
    sub_in_name = parse_name(s[0])
    sub_in_full = find_name(sub_in_name, inlist)
    if s[2]:
        sub_out_full = find_name(sub_out_name, outlist)
    else:
        sub_out_full = ''
    if not s[2] is None:
        w = input('subbing in someone')
        inlist = subs
        outlist = lu['name']
        sub_out_name = parse_name(s[2])
        sublist = None
        if len(lu.index[lu['name'] == sub_out_full].tolist()) > 0:
            lu.iloc[lu.index[lu['name'] == sub_out_full].tolist()[0]] = [lu.iloc[lu.index[lu['name'] == sub_out_full].tolist()[0]]['order'], sub_in_full, pos]
        if pos == 'P':
            lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]] = [lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]]['order'], sub_in_full, pos]
    else:
        w = input('postition change')
        if pos == 'P':
            if input(lu + '\nIs new pitcher in the lineup? (y/n): ') == 'n':
                inlist = subs
            else:
                inlist = lu['name']
            if len(lu[lu['order'] == 'P']['order'].tolist()) == 0:
                lu.loc[9] = ['P', sub_in_full, pos]
            else:
                if len(lu.index[lu['name'] == sub_in_full].tolist()) > 1:
                    lu = lu.drop([9])
                    lu.iloc[lu.index[lu['name'] == sub_in_full].tolist()[0]] = [lu.iloc[lu.index[lu['name'] == sub_in_full].tolist()[0]]['order'], sub_in_full, pos]
                else:
                    lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]] = [lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]]['order'], sub_in_full, pos]
        else:
            inlist = lu['name']
            if len(lu.index[lu['name'] == sub_in_full].tolist()) > 0:
                lu.iloc[lu.index[lu['name'] == sub_in_full].tolist()[0]] = [lu.iloc[lu.index[lu['name'] == sub_in_full].tolist()[0]]['order'], sub_in_full, pos]

####
    # if len(lu.index[lu['name'] == sub_out_full].tolist()) > 0:
    #     lu.iloc[lu.index[lu['name'] == sub_out_full].tolist()[0]] = [lu.iloc[lu.index[lu['name'] == sub_out_full].tolist()[0]]['order'], sub_in_full, pos]
    #     if pos == 'P':
    #         if len(lu.index[lu['order'] == 'P'].tolist()) > 0:
    #             lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]] = [lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]]['order'], sub_in_full, pos]
    #         elif len(lu[lu['order'] == 'P']['order'].tolist()) == 0:
    #             lu.loc[9] = ['P', sub_in_full, 'P']
    # else:
    #     if pos == 'P':
    #         if len(lu.index[lu['order'] == 'P'].tolist()) > 0:
    #             lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]] = [lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]]['order'], sub_in_full, pos]
    #         elif len(lu[lu['order'] == 'P']['order'].tolist()) == 0:
    #             lu.loc[9] = ['P', sub_in_full, 'P']
    #     elif len(lu.index[lu['name'] == sub_in_full].tolist()) > 0:
    #         lu.iloc[lu.index[lu['name'] == sub_in_full].tolist()[0]] = [lu.iloc[lu.index[lu['name'] == sub_in_full].tolist()[0]]['order'], sub_in_full, pos]

    if team == 'home':
        lineups[0] = lu
    else:
        lineups[3] = lu

    if pos == 'PR':
        runners.iloc[runners.index[runners['name'] == sub_out_full].tolist()[0]] = [runners.iloc[runners.index[runners['name'] == sub_out_full].tolist()[0]]['base'],
        sub_in_full, runners.iloc[runners.index[runners['name'] == sub_out_full].tolist()[0]]['resp_pit'], '','','']
    return [lineups, runners]

def is_sub(s: str) -> list:
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
    subtest = re.search(r"^([A-Za-z,\. '-]*?(?= [a-z])|\/) (pinch (?:hit|ran)|to [0-9a-z]{1,2})* *(?:for ([A-Za-z,\. '-]*?)\.$)*", s)
    if not subtest is None:
        subtest = [subtest.group(1), subtest.group(2), subtest.group(3)]
        if not subtest[1] is None:
            return subtest
        return False

def correct_play(play, outs):
    if 'caught stealing, picked off' in play:
        play = play.replace(', picked off','')
    if 'caught stealing' in play and 'stole' in play:
        play = play.replace('stole', '')
    if 'caught stealing' in play and 'advanced' in play and outs %3 == 2:
        play = play.replace('advanced to', '')
    if 'Mervis, M. struck out (1-2): Lux, D. out at second c to ss.' in play:
        play = 'Mervis, M. struck out swinging (1-2): Lux, D. out at second c to ss, caught stealing.'
    play = play.replace(', RBI', ', 1 RBI')
    play = play.replace(', advanced', '; advanced').replace(', scored', '; scored').replace(', out at', '; out at')
    return play

# if 'Dropped foul ball' in play: #need to change this for errors
#     play = 'No Play'
#     skip = True
# # play = play.replace('for WILLIAMS, C.', '.')
# #2/15
# if 'Allen out at second c to 2b.' in play:
#     play = 'Allen out at second c to 2b, caught stealing.'
# if 'D LaManna to c for E Copeland' in play:
#     play = 'D LaManna to c for Zyska'
#2/16
# if 'HIBBITS pinch ran for SCHROEDER.' in play:
#     play = 'HIBBITS pinch hit for SCHROEDER.'
# if 'FIELDS,J. to rf' in play:
#     play = 'Winikur to rf'

def get_batter(lineup, order: int) -> str:
    """
    returns current batter based on position in the batting order

    Parameters
    ----------
    lineup : df
        dataframe of lineup with columns 'order', 'name', 'position'
    Returns
    -------
    str
        full name of the player up to bat
    """
    return [lineup['name'].iloc[order-1], lineup['position'].iloc[order-1]]

def get_off_lineups(inn_half, lineups) -> list:
    """
    returns corresponding team lineup and substitutions
    Parameters
    ----------
    lineups : list
        a list containing home and away lineups and subs:
        [home_lineup, home_subs, store_hm_order,
        away_lineup, away_subs, store_aw_order]
    inn_half : int
        0: top half of inning
        1: bottom half of inning
    """
    if inn_half == 0:
        order = lineups[5]
        lineup = lineups[3]
    elif inn_half == 1:
        order = lineups[2]
        lineup = lineups[0]
    return [order, lineup]

def get_def_lineups(inn_half, lineups) -> list:
    """
    returns corresponding team lineup and substitutions
    Parameters
    ----------
    lineups : list
        a list containing home and away lineups and subs:
        [home_lineup, home_subs, store_hm_order,
        away_lineup, away_subs, store_aw_order]
    inn_half : int
        0: top half of inning
        1: bottom half of inning
    """
    if inn_half == 1:
        order = lineups[5]
        lineup = lineups[3]
    elif inn_half == 0:
        order = lineups[2]
        lineup = lineups[0]
    return [order, lineup]

def get_event_type(s: str, batter: str, runners, lineup):
    """
    returns 'BAT' or 'RUN' based on whether the first name in the first
    index of the play by play list matches the current batter

    Parameters
    ----------
    batter : str

    Returns
    -------
    'BAT': play contains a batter event
    'RUN': play contains only a runner event
    """
    if find_name(parse_name(get_name(s)), lineup) == runners.loc[0,'name']:
        return 'BAT'
    else:
        return 'RUN'

def parse_bat(s, batter, runners): #s is index 0 of split play
    event = s.split(';')[0]
    short_event = re.search(r'([sdth][a-z]{3}[rl]ed)|([a-z]*ed out)|out at first|popped up|infield fly|(struck out *[a-z]*)|error|(fielder\'s choice)|walked|(hit by pitch)|(\w* into \w* play)|((batter\'s|catcher\'s) interference)', s)
    if not short_event is None and short_event != '':
        short_event = short_event.group()
        if short_event in codes:
            event_abb = codes[short_event]
            if event_abb in event_codes:
                event_cd = event_codes[event_abb]
                if event_cd in {14, 15, 16, 17, 18, 19, 20}: #BB, IBB, HBP, C, E, FC, 1B
                    dest = 1
                elif event_cd ==  21: #2B
                    dest = 2
                elif event_cd ==  22: #3B
                    dest = 3
                elif event_cd ==  23: #HR
                    dest = 4
                elif event_cd == 3: #K
                    if 'reached first' in s:
                        dest = 1
                    else: #out
                        dest = 0
                elif event_cd == 2:
                    dest = 0
        batter_adv = s.split('; ')[1:]
        if not batter_adv == []:
            for adv in batter_adv:
                adv_txt = re.search(r'(advanced to [a-z]*)|((scored) on (the throw)|(advanced on an error by [a-z0-9]{1,2}))|(out at [a-z]* [0-9a-z]{1,2}(?: to [0-9a-z]{1,2})*)', adv)
                if not adv_txt is None:
                    adv_txt = adv_txt.group()
            #parse adv_txt, add to list -- add adv_event_cd somewhere
            #Ex: Groshans, J. struck out swinging, reached first on a passed ball, advanced to second (3-2 FBBBFFS): Karre, R. advanced to third on a passed ball, scored, unearned.
            b_outcome = re.search(r"(advanced to \w*|scored|out at \w*)(?!.*(advanced|scored|out))", s).group()
            if 'advanced' in b_outcome:
                dest = base_codes[re.search(r'(?<=advanced to )\w*', b_outcome).group()]
            if 'out at' in b_outcome:
                dest = 0
            elif 'scored' in b_outcome:
                dest = 4
        else:
            b_outcome = ''
            batter_adv = ''
        runners.loc[0, 'dest'] = dest
    else:
        fixed = input('play: ' + s + '\nType corrected play text: ')
        parse_bat(fixed, batter, runners)
    return [event_cd, runners] #parse_def(event, event_cd)

#def parse_error(s: str) -> list:
    """
    returns the position charged with the error and error type

    Parameters
    ----------
    s : str
        string containing play by play text containing an error

    Returns
    -------
    list
        list containing [code of fielder charged with error, error type - T: Throwing, F: Fielding]

    """
    err_type = re.search(r'(?<=a )[a-z]*(?= error)', s)
    if not err_type is None:
        err_type = err_type.group()
    else:
        err_type = 'fielding'
    if 'throwing' in err_type:
        type = 'T'
    else:
        type = 'F'
    err_by = (re.search(r'(?<=error by) [0-9a-z]{1,2}', s).group()).upper()
    err_fld_cd = fielder_codes[err_by]
    return [err_fld_cd, type]

def event_flags(s, event_cd, event_outs, batter_of_inn, runners):
    leadoff_fl = False
    ab_fl = False
    hit_fl = False
    event_fl = False
    sf_fl = False
    sh_fl = False
    bunt_fl = False
    wp_fl = False
    pb_fl = False
    dp_fl = False
    tp_fl = False
    [run1_sb_fl, run2_sb_fl, run3_sb_fl] = [False, False, False]
    [run1_cs_fl, run2_cs_fl, run3_cs_fl] = [False, False, False]
    [run1_pk_fl, run2_pk_fl, run3_pk_fl] = [False, False, False]

    if batter_of_inn == 1:
        leadoff_fl = True
    if event_cd in {2,3,18,19,20,21,22,23}:
        ab_fl = True
    if event_cd in {20,21,22,23}:
        hit_fl = True
    if event_cd in range(1,25):
        event_fl = True
    if 'SF' in s:
        sf_fl = True
    if 'SAC' in s:
        sh_fl = True
    if 'bunt' in s:
        bunt_fl = True
    if 'wild pitch' in s:
        wp_fl = True
    if 'passed ball' in s:
        pb_fl = True
    if event_outs == 2:
        dp_fl = True
    if event_outs == 3:
        tp_fl = True

    run1_ev_cd = runners.loc[1,'event_cd']
    run2_ev_cd = runners.loc[2,'event_cd']
    run3_ev_cd = runners.loc[3,'event_cd']
    if run1_ev_cd == '4':
        run1_sb_fl = True
    elif run1_ev_cd == '6':
            run1_cs_fl = True
    elif run1_ev_cd == '8':
            run1_pk_fl = True
    if run2_ev_cd == '4':
        run2_sb_fl = True
    elif run2_ev_cd == '6':
            run2_cs_fl = True
    elif run2_ev_cd == '8':
            run2_pk_fl = True
    if run3_ev_cd == '4':
        run3_sb_fl = True
    elif run3_ev_cd == '6':
            run3_cs_fl = True
    elif run3_ev_cd == '8':
            run3_pk_fl = True
    return [ab_fl, hit_fl, event_fl, sf_fl, sh_fl, bunt_fl, wp_fl, pb_fl, dp_fl, tp_fl, run1_sb_fl, run2_sb_fl, run3_sb_fl, run1_cs_fl, run2_cs_fl, run3_cs_fl, run1_cs_fl, run2_cs_fl, run3_cs_fl]

def sub_flags():
    pass

def parse_run(s: str, runners):
    runner = parse_name(get_name(s))
    runner_full = find_name(runner, runners.loc[:,'name'])
    runner_base = runners.index[runners['name'] == runner_full].tolist()[0]
    # run_list = s.split('; ')
    run_event = re.search(r'stole [a-z]*|advanced to \w* on (?:a )*(wild pitch|passed ball|balk|defensive indifference)|advanced to \w* on an error by p, failed pickoff attempt|scored on (?:a )*(wild pitch|passed ball|balk|defensive indifference)|out at .*(picked off|caught stealing)', s)
    if not run_event is None:
        run_event = run_event.group()
        run_short_event = re.search(r'stole|wild pitch|passed ball|balk|defensive indifference|picked off|caught stealing|error', run_event)
        if not run_short_event is None:
            run_short_event = run_short_event.group()
        if run_short_event in codes:
            run_abb = codes[run_short_event]
            if run_abb in event_codes:
                run_event_cd = event_codes[run_abb]
            else:
                run_event_cd = input('play: ' + s + '\nEnter runner event code: ')
    else:
        run_event_cd = ''
    runner_outcome = re.search(r"(stole \w*|advanced to \w*|scored|out at \w*)(?!.*(advanced|scored|out))", s)
    if not runner_outcome is None:
        runner_outcome = runner_outcome.group()
    elif 'out on the play' in s:
        runner_outcome = 'out on the play'
    else:
        runner_outcome = ''
    if 'advanced' in runner_outcome:
        dest = base_codes[re.search(r'(?<=advanced to )\w*', runner_outcome).group()]
    elif 'scored' in runner_outcome:
        dest = 4
        if 'unearned' in s:
            runners.loc[runner_base, 'resp_pit'] = ''
    elif 'stole' in runner_outcome:
        dest = base_codes[re.search(r'(?<=stole )\w*', runner_outcome).group()]
        run_abb = run_abb + '/' + str(base_codes[re.search(r'(?<=stole )\w*', runner_outcome).group()])
    elif 'out' in runner_outcome:
        dest = 0
    else:
        dest = input('play: ' + s + '\nInput destination for runner ' + runner_full + ": ")
    runners.loc[runner_base, 'dest'] = dest
    runners.loc[runner_base, 'event_cd'] = run_event_cd
    return [runners, runner_full, run_event_cd] #eventually run_abb

def advance_runners(runners, score, inn_half):
    """
    moves runners after play corresponding to destinations

    Parameters
    ----------

    Returns
    -------

    """
    # runners = pd.DataFrame([[0,'Trout, Mike','Jansen, Kenley','2','','21'], [1,'Calhoun, Kole','Kershaw, Clayton','0','94',''], [2,'','','','',''], [3,'La Stella, Tommy','Kershaw, Clayton','4','','']], columns = ['base', 'name', 'resp_pit', 'dest', 'play','event_cd'])
    event_outs = 0
    [home_score, away_score] = score
    new_runners = pd.DataFrame([[0,'','','','',''], [1,'','','','',''], [2,'','','','',''], [3,'','','','','']], columns = ['base', 'name', 'resp_pit', 'dest', 'play','event_cd'])
    for base in range(0,4):
        br = runners.loc[3-base, 'name']
        pit = runners.loc[3-base, 'resp_pit']
        if  br != '':
            if runners.loc[3-base, 'dest'] == '':
                runners.loc[3-base, 'dest'] = 3-base
            dest = int(runners.loc[3-base, 'dest'])
            if dest > 0 and dest < 4:
                new_runners.loc[dest, 'name'] = br
                new_runners.loc[dest, 'resp_pit'] = pit
            if dest != 3-base and dest != 5:
                new_runners.loc[3-base, 'name'] = ''
            if dest == 4:
                if inn_half == 0:
                    away_score += 1
                else:
                    home_score += 1
            if dest == 0:
                event_outs += 1
    runners = new_runners
    return [runners, [home_score, away_score], event_outs]

# def get_out_loc(s, type):
#     if type in ['F', 'L', 'P']:
#         out_location = re.search(r'(?<=out to )[0-9a-z]{1,2}', s)
#         if not out_location is None:
#             out_location = out_location.group()
#         else:
#             out_location = input('Enter out location: ')
#     elif type == 'FC':
#
#     elif type == 'DP':
#
#     elif type == 'TP':
#
#     elif type == 'G':
#
#     return out_location
#
# def parse_def(s, event_cd):
#     if event_cd in {20,21,22,23}:
#         loc = re.search(r'(to [a-z]*(?: *[a-z]*)*|up [a-z]* [a-z]*|down [a-z]* [a-z]* [a-z0-9]* *[a-z]*|through [a-z]* [a-z]* [a-z]*)', s)
#         bb_loc = loc_codes[loc]
#     elif event_cd == 19:
#         out_loc =
#     elif event_cd == 18:
#         error = parse_error(s)
#     elif event_cd == 2:
#         if 'double play' in s:
#         elif 'triple play' in s:
#         elif 'grounded' in s:
#         elif 'out at first' in s: #1b to p or 2b to p etc
#             fld = re.search(r'(?:out at (?:first|second|third|home) )([a-z0-9]{1,2})(?:(?: to )([a-z0-9]{1,2}))?(?:(?: to )([a-z0-9]{1,2}))?(?:(?: to )([a-z0-9]{1,2}))?(?:(?: to )([a-z0-9]{1,2}))?')
#             fld_list = []
#             for g in range(1,6):
#                 if not fld.group(g) is None:
#                     fld_list.append(fld.group(g))
#
#         else:
#             if 'flied' in s:
#                 type = 'F'
#             elif 'popped' in s:
#                 type = 'P'
#             elif 'grounded' in s:
#                 type = 'G'
#             elif 'lined' in s:
#                 type = 'L'
#             elif 'fouled' in s:
#                 if out_location == 7 or out_location == 9:
#                     type = 'F'
#                 else:
#                     type = 'P'
#                 foul_fl = True
#             out_loc = get_out_loc(s, type)
#             if foul_fl = True
#             out_loc = out_loc + 'F'
#         else:
#
#     elif event cd == 3:

def get_pitches(s): #input from play
    p = re.search(r'\(.+?\)', s)
    if p is not None:
        return p.group()
    else:
        return ''

def get_count(p): #input from pitches()
    s = re.search(r'(?<=-)[0-2]', p)
    b = re.search(r'[0-3](?=-)', p)
    seq = re.search(r'[A-Z]*(?=\))', p) #add an X as necessary to output file --- S11>B.MF2*BX for if we have when in the count a steal happened or pb
    if not s is None and not b is None:
        if not seq is None:
            return [b.group(), s.group(), seq.group()]
        else:
            return [b.group(), s.group(), None]
    else:
        return ['','','']

def get_rbi(s: str) -> int:
    """
    return number of RBI in the play

    Parameters
    ----------
        s : str
            text of the play

    Returns
    -------
    int
        number of rbi
    """
    if 'RBI' in s:
        return int(re.search(r'[1-4]*(?= RBI)', s).group())

def get_defense(inn_half, lineups) -> list: #lineup input from get_lineups
    """
    returns list of names in order of positions

    Parameters
    ----------
    lu : df
        dataframe containing team's lineup with cols 'order', 'name', 'position'

    Returns
    -------
    list
        names of players in defensive positional order: [P,C,1B,2B,3B,SS,LF,CF,RF]
    """
    lu = get_def_lineups(inn_half, lineups)[1]
    return [lu[lu['position'] == 'P'].iloc[0]['name'],
        lu[lu['position'] == 'C'].iloc[0]['name'],
        lu[lu['position'] == '1B'].iloc[0]['name'],
        lu[lu['position'] == '2B'].iloc[0]['name'],
        lu[lu['position'] == '3B'].iloc[0]['name'],
        lu[lu['position'] == 'SS'].iloc[0]['name'],
        lu[lu['position'] == 'LF'].iloc[0]['name'],
        lu[lu['position'] == 'CF'].iloc[0]['name'],
        lu[lu['position'] == 'RF'].iloc[0]['name']
    ]

def parse_pbp(play_list, lineups, inn_half, runners):
    try:
        [order, lu] = get_off_lineups(inn_half, lineups)
        [batter, bat_pos] = get_batter(lu, order)
        defense = get_defense(inn_half, lineups)
        runners.loc[0, 'name'] = batter
        runners.loc[0, 'resp_pit'] = defense[0]
        batter_event_fl = False
        for play in play_list:
            print(play)
            print(batter)
            print(runners.loc[:,'name':'dest'])
            event_type = get_event_type(play, batter, runners, lu.loc[:,'name'])
            if event_type == 'BAT':
                [event_cd, runners] = parse_bat(play, batter, runners)
                batter_event_fl = True
            else:
                [runners, runner_full, run_event_cd] = parse_run(play, runners)
                if not batter_event_fl:
                    event_cd = run_event_cd
        if not batter_event_fl:
            runners.loc[0, 'dest'] = 5
        return [runners, event_cd, batter_event_fl, batter, bat_pos, order, defense]
    except:
        return None

def inc_bat_order(lineups, inn_half):
    if inn_half == 1:
        lineups[2] += 1
        if lineups[2] == 10:
            lineups[2] = 1
    else:
        lineups[5] += 1
        if lineups[5] == 10:
            lineups[5] = 1
    return lineups


#TESTS:
# home_lineup = pd.DataFrame([[1, 'Kennedy, Eric', 'LF'], [2, 'Ellis, Duke', 'CF'], [3, 'Ford, Lance', '2B'],
# [4, 'Zubia, Zach', 'DH'], [5, 'McCann, Michael', 'C'], [6, 'Todd, Austin', 'RF'],
# [7, 'Reynolds, Ryan', '3B'], [8, 'Shaw, Tate', '1B'], [9, 'Hibbeler, Masen', 'SS'], ['P', 'Elder, Bryce', 'P']], columns = ['order', 'name', 'position'])
# home_subs = ['Fields, Kamron', 'Quintanilla, Cole']
# away_lineup = pd.DataFrame([[1, 'Vujovich, Jordan', 'LF'], [2, 'Treadaway, Tanner', 'CF'], [3, 'Ware, Brylie', '3B'],
# [4, 'Lindsly, Brady', 'DH'], [5, 'Mitchell, Justin', 'C'], [6, 'Hardman, Tyler', '1B'],
# [7, 'Zaragoza, Brandon', 'SS'], [8, 'Harlan, Brady', 'RF'], [9, 'McKenna, Conor', '2B'], ['P', 'Abram, Ben', 'P']], columns = ['order', 'name', 'position'])
# away_subs = ['Smith, Ledgend', 'Olds, Wyatt']
# lineups = [home_lineup, home_subs, 1, away_lineup, away_subs, 1]
#
# runners = pd.DataFrame([[0,'','','','',''], [1,'','','','',''], [2,'','','','',''], [3,'','','','','']], columns = ['base', 'name', 'resp_pit', 'dest', 'play','event_cd']) #play is the play made on the runner if out e.g. 43 for 2b to 1b
#
# state = [0,0,1,0,0,runners]
# [away_score, home_score, inn, inn_half, outs, runners] = state
#
# runners.loc[2,'resp_pit'] = 'Elder, Bryce'
# runners
#
# lineups
# sub = is_sub('McCann to c.')
# pbp_txt = ''
# lineups = make_sub(sub, lineups, inn_half)
# lineups
# pbp_txt = 'Vujovich, J. struck out swinging, reached first on a passed ball, advanced to second (3-2 FBBBFFS): McKenna, C. advanced to third on a passed ball, scored, unearned.'
# sub = is_sub(pbp_txt)
# play_list = pbp_txt.split(": ")
# play_list
#
# out = parse_pbp(play_list, lineups, inn_half)
# [order, lu] = get_off_lineups(inn_half, lineups)
# lu
# event_type = get_event_type(play_list[0], get_batter(lu, order), runners, lu.loc[:,'name'])
# event_type
# parse_bat(play_list[0], get_batter(lu, order), runners)
# s = play_list[0]
# s
# parse_run(s, runners)


def parse_play(line, state, meta, lineups, event_no, response):
    try:
        [home_score, away_score, inn, inn_half, outs, runners, batter_of_inn] = state
        score = [home_score, away_score]

        [game_id, home_abb, away_abb, ump] = meta

        [pbp_txt, line, end] = get_pbp(response, inn_half, inn, line)
        if end:
            return [True] #other stuff maybe?
        [balls, strikes, seq] = get_count(pbp_txt)

        sub = is_sub(pbp_txt)
        if sub:
            batter_event_fl = False
            event_fl = False
            [lineups, runners] = make_sub(sub, lineups, inn_half, runners)
            return[end, lineups, 0, line+1, batter_event_fl, event_fl, outs, score, runners, []]
        else:
            pbp_txt = correct_play(pbp_txt, outs)
            play_list = pbp_txt.split(": ")
            [runners, event_cd, batter_event_fl, batter, bat_pos, order, defense] = parse_pbp(play_list, lineups, inn_half, runners)
            # [pos]
            #add - find positions of hitter and runners (ph/pr tag)
            if batter_event_fl: #from return of parse play
                lineups = inc_bat_order(lineups, inn_half)
            # game_id
            # home_abb
            # away_abb
            # inning
            # inn_half
            # inn_outs
            # balls
            # strikes
            # seq
            # away_score
            # home_score
            # batter
            # BAT_HAND_CD
            # RESP_BAT_ID
            # RESP_BAT_HAND_CD
            # pitcher
            # PIT_HAND_CD
            # RESP_PIT_ID
            # RESP_PIT_HAND_CD
            [pitcher, pos2_id, pos3_id, pos4_id, pos5_id, pos6_id, pos7_id, pos8_id, pos9_id] = defense
            # pos2_id
            # pos3_id
            # pos4_id
            # pos5_id
            # pos6_id
            # pos7_id
            # pos8_id
            # pos9_id
            base1_run = runners.loc[1,'name']
            base2_run = runners.loc[2,'name']
            base3_run = runners.loc[3,'name']
            # EVENT_TX
            # LEADOFF_FL
            if bat_pos == 'PH':
                ph_fl =  True
            else:
                ph_fl = False
            batter_pos = fielder_codes[bat_pos]
            # order
            # event_cd
            # bat_event_fl
            # ab_fl
            # h_fl
            # sh_fl
            # sf_fl
            # event_outs
            # dp_fl
            # tp_fl
            rbi = get_rbi(pbp_txt)
            # wp_fl
            # pb_fl
            # FLD_CD
            # BATTEDBALL_CD
            # bunt_fl
            # foul_fl
            # BATTEDBALL_LOC_TX
            # ERR_CT
            # ERR1_FLD_CD
            # ERR1_CD
            # ERR2_FLD_CD
            # ERR2_CD
            # ERR3_FLD_CD
            # ERR3_CD
            bat_dest = runners.loc[0,'dest']
            run1_dest = runners.loc[1,'dest']
            run2_dest = runners.loc[2,'dest']
            run3_dest = runners.loc[3,'dest']
            # BAT_PLAY_TX
            # RUN1_PLAY_TX
            # RUN2_PLAY_TX
            # RUN3_PLAY_TX
            # run1_sb_fl
            # run2_sb_fl
            # run3_sb_fl
            # run1_cs_fl
            # run2_cs_fl
            # run3_cs_fl
            # run1_pk_fl
            # run2_pk_fl
            # run3_pk_fl
            run1_resp_pit = runners.loc[1, 'resp_pit']
            run2_resp_pit = runners.loc[2, 'resp_pit']
            run3_resp_pit = runners.loc[3, 'resp_pit']
            # GAME_NEW_FL
            # GAME_END_FL
            # PR_RUN1_FL -- add column to runners
            # PR_RUN2_FL
            # PR_RUN3_FL
            # REMOVED_FOR_PR_RUN1_ID
            # REMOVED_FOR_PR_RUN2_ID
            # REMOVED_FOR_PR_RUN3_ID
            # REMOVED_FOR_PH_BAT_ID
            # REMOVED_FOR_PH_BAT_FLD_CD
            # PO1_FLD_CD
            # PO2_FLD_CD
            # PO3_FLD_CD
            # ASS1_FLD_CD
            # ASS2_FLD_CD
            # ASS3_FLD_CD
            # ASS4_FLD_CD
            # ASS5_FLD_CD
            # EVENT_ID

            [new_runners, score, event_outs] = advance_runners(runners, score, inn_half)
            inn_outs = outs + event_outs
            [ab_fl, hit_fl, event_fl, sf_fl, sh_fl, bunt_fl, wp_fl, pb_fl, dp_fl, tp_fl, run1_sb_fl, run2_sb_fl, run3_sb_fl, run1_cs_fl, run2_cs_fl, run3_cs_fl, run1_pk_fl, run2_pk_fl, run3_pk_fl] = event_flags(pbp_txt, event_cd, event_outs, batter_of_inn, runners)
            #need leadoff flag
            play_out = [end, lineups, event_outs, line+1, batter_event_fl, event_fl, inn_outs, score, new_runners, [game_id, home_abb, away_abb, inn,
            inn_half, outs, balls, strikes, seq, away_score, home_score, batter, pitcher,
            pos2_id, pos3_id, pos4_id, pos5_id, pos6_id, pos7_id, pos8_id, pos9_id,
            base1_run, base2_run, base3_run, event_cd, ph_fl, batter_pos, order, event_cd,
            batter_event_fl, ab_fl, hit_fl, sh_fl, sf_fl, event_outs, dp_fl, tp_fl,
            rbi, wp_fl, pb_fl, bunt_fl, bat_dest, run1_dest, run2_dest, run3_dest, run1_resp_pit, run2_resp_pit, run3_resp_pit,
            run1_sb_fl, run2_sb_fl, run3_sb_fl, run1_cs_fl, run2_cs_fl, run3_cs_fl, run1_pk_fl, run2_pk_fl, run3_pk_fl, event_no, pbp_txt]]

            return play_out
    except:
            return None


class PbpspiderSpider(scrapy.Spider):
    name = 'pbpspider'
    allowed_domains = ["stats.ncaa.org"]

    def start_requests(self):
        urls = []
        d = input('Enter date in format yyyy-mm-dd: ')
        urls.append("https://stats.ncaa.org/season_divisions/16800/scoreboards?game_date=" + d[5:7] + "%2F" + d[8:10] + "%2F" + d[0:4])
        for url in urls:
            yield SplashRequest(
                url = url,
                callback = self.game_page,
                endpoint='render.html',
                args={'wait': .1},
            )

    def game_page(self, response):
        links = response.xpath("//div[@id='contentarea']/table/tbody/tr/td[1]/a[@class='skipMask']/@href").getall()
        for link in links:
            abs_url = response.urljoin(link)
            yield SplashRequest(
                url = abs_url,
                callback = self.box_check,
                endpoint='render.html',
                args={'wait': .05}
                )

    def box_check(self, response):
        box = response.xpath("//div[@id='primary_nav_wrap']/ul[@id='root']/li[1]/a/@href").get()
        boxurl = response.urljoin(box)
        yield SplashRequest(
            url = boxurl,
            callback = self.lineups,
            endpoint = 'render.html',
            args = {'wait':.05}
        )

    def lineups(self, response):
        h = scrape_lineups('home', response)
        a = scrape_lineups('away', response)
        home_lineup = h[0]
        away_lineup = a[0]
        home_subs = h[1]
        away_subs = a[1]

        yield SplashRequest(
                url = response.urljoin(response.xpath("//ul[@id='root']/li[3]/a/@href").get()),
                callback = self.parsegame,
                endpoint = 'render.html',
                args = {'wait':.1},
                meta={"away_lineup": away_lineup, "home_lineup": home_lineup, "away_subs": away_subs, "home_subs": home_subs}
                )

    def parsegame(self, response):
        away_lineup = response.meta["away_lineup"]
        home_lineup = response.meta["home_lineup"]
        home_subs = response.meta["home_subs"]
        away_subs = response.meta["away_subs"]
        play_info = []
        away_score = 0
        home_score = 0

        store_hm_order = 1
        store_aw_order = 1

        innings = response.xpath("//tr[@class='heading']/td[1]/a/text()").getall()[-1] #last listed inning
        last = innings[0:len(innings)-9] #numeric value for last listed inning
        away = response.xpath("//table[@class='mytable'][1]/tbody/tr[2]/td[1]/a/text()").get() #away team
        home = response.xpath("//table[@class='mytable'][1]/tbody/tr[3]/td[1]/a/text()").get() #home team
        ump = re.search(r'(?<=hp:)\W*(\w* \w*)', response.xpath("//table[4]/tbody/tr/td[2]/text()[1]").get())
        if not ump is None:
            ump = ump.group(1)
        else:
            ump = ''
        date = response.xpath("//div[@id='contentarea']/table[3]/tbody/tr[1]/td[2]/text()").get()[9:19]
        date = date.replace('/', '')
        if len(teamindex[teamindex['school'] == home]) < 1:
            home_abb = home
        else:
            home_abb = teamindex[teamindex['school'] == home].iloc[0]['abbreviation']
        if len(teamindex[teamindex['school'] == away]) < 1:
            away_abb = away
        else:
            away_abb = teamindex[teamindex['school'] == away].iloc[0]['abbreviation']

        end = False
        game_id = date + away_abb + home_abb
        lineups = [home_lineup, home_subs, store_hm_order, away_lineup, away_subs, store_aw_order]
        meta = [game_id, home_abb, away_abb, ump]
        ###LOOP THROUGH INNINGS###
        event_no = 1
        for inn in range(1, int(last)+1):
            line = 2
            for inn_half in range(0,2):
                batter_of_inn = 0
                outs = 0
                runners = pd.DataFrame([[0,'','','','',''], [1,'','','','',''], [2,'','','','',''], [3,'','','','','']],
                columns = ['base', 'name', 'resp_pit', 'dest', 'play','event_cd'])
                while outs < 3:
                    try:
                        state = [home_score, away_score, inn, inn_half, outs, runners, batter_of_inn]
                        print(home_abb + ': ' + str(state[0]) + ' ' + away_abb + ': ' + str(state[1]) + ' inning: ' + str(inn) + ' outs: ' + str(outs))
                        print(get_pbp(response, inn_half, inn, line))
                        play_out = parse_play(line, state, meta, lineups, event_no, response)
                        # lineups, event_outs, line, batter_event_fl, event_fl, inn_outs, score, new_runners, end,
                        end = play_out[0]
                        if end:
                            break
                        [home_score, away_score] = play_out[7]
                        outs = play_out[6]
                        lineups = play_out[1]
                        if play_out[4]:
                            batter_of_inn += 1
                        line = play_out[3]
                        if play_out[5]:
                            play_info.append(play_out[9])
                            event_no += 1
                        runners = play_out[8]
                    except:
                        line+=1
                        continue
                if end:
                    break

        df=pd.DataFrame(play_info, columns=['game_id', 'home_abb', 'away_abb', 'inning',
        'inn_half', 'outs', 'balls', 'strikes', 'seq', 'away_score', 'home_score', 'batter', 'pitcher',
        'pos2_id', 'pos3_id', 'pos4_id', 'pos5_id', 'pos6_id', 'pos7_id', 'pos8_id', 'pos9_id',
        'base1_run', 'base2_run', 'base3_run', 'event_abb', 'ph_fl', 'batter_pos', 'order', 'event_cd',
        'batter_event_fl', 'ab_fl', 'hit_fl', 'sh_fl', 'sf_fl', 'event_outs', 'dp_fl', 'tp_fl',
        'rbi', 'wp_fl', 'pb_fl', 'bunt_fl', 'bat_dest', 'run1_dest', 'run2_dest', 'run3_dest', 'run1_resp_pit', 'run2_resp_pit', 'run3_resp_pit',
        'run1_sb', 'run2_sb', 'run3_sb', 'run1_cs', 'run2_cs', 'run3_cs', 'run1_pk', 'run2_pk', 'run3_pk', 'event_no', 'pbp_text'])

        df.to_csv('.././pbp/' + date +'.csv', mode='a', index=False, header=False)




"""
GAME_ID
AWAY_TEAM_ID
INN_CT
BAT_HOME_ID
OUTS_CT
BALLS_CT
STRIKES_CT
PITCH_SEQ_TX
AWAY_SCORE_CT
HOME_SCORE_CT
BAT_ID
BAT_HAND_CD
RESP_BAT_ID
RESP_BAT_HAND_CD
PIT_ID
PIT_HAND_CD
RESP_PIT_ID
RESP_PIT_HAND_CD
POS2_FLD_ID
POS3_FLD_ID
POS4_FLD_ID
POS5_FLD_ID
POS6_FLD_ID
POS7_FLD_ID
POS8_FLD_ID
POS9_FLD_ID
BASE1_RUN_ID
BASE2_RUN_ID
BASE3_RUN_ID
EVENT_TX
LEADOFF_FL
PH_FL
BAT_FLD_CD
BAT_LINEUP_ID
EVENT_CD
BAT_EVENT_FL
AB_FL
H_FL
SH_FL
SF_FL
EVENT_OUTS_CT
DP_FL
TP_FL
RBI_CT
WP_FL
PB_FL
FLD_CD
BATTEDBALL_CD
BUNT_FL
FOUL_FL
BATTEDBALL_LOC_TX
ERR_CT
ERR1_FLD_CD
ERR1_CD
ERR2_FLD_CD
ERR2_CD
ERR3_FLD_CD
ERR3_CD
BAT_DEST_ID
RUN1_DEST_ID
RUN2_DEST_ID
RUN3_DEST_ID
BAT_PLAY_TX
RUN1_PLAY_TX
RUN2_PLAY_TX
RUN3_PLAY_TX
RUN1_SB_FL
RUN2_SB_FL
RUN3_SB_FL
RUN1_CS_FL
RUN2_CS_FL
RUN3_CS_FL
RUN1_PK_FL
RUN2_PK_FL
RUN3_PK_FL
RUN1_RESP_PIT_ID
RUN2_RESP_PIT_ID
RUN3_RESP_PIT_ID
GAME_NEW_FL
GAME_END_FL
PR_RUN1_FL
PR_RUN2_FL
PR_RUN3_FL
REMOVED_FOR_PR_RUN1_ID
REMOVED_FOR_PR_RUN2_ID
REMOVED_FOR_PR_RUN3_ID
REMOVED_FOR_PH_BAT_ID
REMOVED_FOR_PH_BAT_FLD_CD
PO1_FLD_CD
PO2_FLD_CD
PO3_FLD_CD
ASS1_FLD_CD
ASS2_FLD_CD
ASS3_FLD_CD
ASS4_FLD_CD
ASS5_FLD_CD
EVENT_ID
"""
