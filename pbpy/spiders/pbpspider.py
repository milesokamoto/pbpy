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
    'p' : 1,
    'c' : 2,
    '1b' : 3,
    '2b' : 4,
    '3b' : 5,
    'ss' : 6,
    'lf' : 7,
    'cf' : 8,
    'rf' : 9,
    'dh' : 10,
    'ph' : 11
}
base_codes = {
    'first': 1,
    'second': 2,
    'third': 3,
    'home': 4,
    'scored': 4,
    'out': 0
}
def get_lineups(team: str, response) -> list:
    """
    Parameters
    ----------
    team : str
        'home' or 'away'
    response :
        webpage response
    """

    end = False
    lineup = []
    subs = []
    i = 1
    order = 1
    if team == 'home':
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
    return [pd.DataFrame(lineup, columns = ['order', 'name', 'position']), subs]

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
        return input('Enter player name: ')

def get_sub_name(s: str, type: str) -> str:
    """
    extracts sub name
    Parameters
    ----------
    s : str
        substitution text
    type : str
        sub type: 'PH' for pinch hitter, 'PR' for pinch runner, or 'DEF' for defensive
    """
    if type == 'PH':
        return re.search(r"([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*(?= | [a-z])(?= pinch hit for)", s).group()
    elif type == 'PR':
        return re.search(r"([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*(?= | [a-z])(?= pinch ran for)", s).group()
    elif type == 'DEF':
        return = re.search(r"([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*(?= | [a-z])(?= to [0-9a-z]{1,2})", s).group()

def get_subs(lineups: list, subtype: str) -> list:
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
        2 elements: [dataframe of lineup (order, name, position), substitution list]
    """
    if subtype == 'OFF':
        if inn_half == 0:
            lu = lineups[3]
            subs = lineups[4]
        else:
            lu = lineups[0]
            subs = lineups[1]
    else:
        if inn_half == 0:
            lu = lineups[2]
            subs = lineups[3]
        else:
            lu = lineups[2]
            subs = lineups[3]
    return [lu, subs]

def get_pos(s: str) -> str:
    """
    extracts position from substitution text
    Parameters
    ----------
    s : str
        string containing substitution text
    """
    if 'hit' in s[1]:
        return 'PH'
    elif 'ran' in s[1]:
        return 'PR'
    else:
        return (re.search(r'(?<= to )[0-9a-z]{1,2}', s).group()).upper()

def parse_name(name: str) -> str:
    """
    reformats name
    Parameters
    ----------
    name : str
        name extracted from pbp text
    """
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
    if 'De La ' in name or 'van ' in name and not ',' in name:
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
            full = input('Input name of player or "reset play" to input new play: ') ##implement "reset play"
    return full

def sub(s: list, lu: df, subs: list) -> list:
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
        new lineup

    """
    if '/' in s[0]:
        s[0] = lu[lu['position']=='P'].iloc[0]['name']
        s[1] = ' to p'

    if 'pinch' in s[1]:
        subtype = 'OFF'
    else:
        subtype = 'DEF'

    sublists = get_subs(lineups, subtype)
    lu = sublists[0]
    subs = sublists[1]
    pos = get_pos(s[1])
    sub_in_name = parse_name(s[0])
    #distinguish between positional changes and defensive subs
    if s[2] is None:
        inlist = lu['name']
    else:
        inlist = subs
        outlist = lu['name']
        sub_out_name = parse_name(s[2])
        sublist = None

    sub_in_full = find_name(sub_in_name, inlist)
    # if sub_in_full == 'team':
    #     if subtype == 'OFF':
    #         sublists = get_subs(lineups, 'DEF')
    #         if s[2] is None:
    #             inlist = lu['name']
    #         else:
    #             inlist = subs
    #             outlist = lu['name']
    #             sub_out_name = parse_name(s[2])
    #             sublist = None
    #     else:
    #         sublists = get_subs(lineups, 'OFF')
    #         if s[2] is None:
    #             inlist = lu['name']
    #         else:
    #             inlist = subs
    #             outlist = lu['name']
    #             sub_out_name = parse_name(s[2])
    #     sub_in_full = find_name(sub_in_name, inlist)

    if s[2]:
        sub_out_full = find_name(sub_out_name, outlist)

    if len(lu.index[lu['name'] == sub_out_full].tolist()) > 0:
        lu.iloc[lu.index[lu['name'] == sub_out_full].tolist()[0]] = [lu.iloc[lu.index[lu['name'] == sub_out_full].tolist()[0]]['order'], sub_in_full, pos]
        if pos == 'P':
            if len(lu.index[lu['order'] == 'P'].tolist()) > 0:
                lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]] = [lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]]['order'], subfull, pos]
            elif len(lu[lu['order'] == 'P']['order'].tolist()) == 0:
                lu.loc[9] = ['P', sub_in_full, 'P']
    return lu

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
    """
    s = 'ELLIS to cf.'
    subtest = re.search(r"^([A-Za-z,\. '-]*?(?= [a-z])|\/) (pinch (?:hit|ran)|to [0-9a-z]{1,2})* *(?:for ([A-Za-z,\. '-]*?)\.$)*", s)
    if not subtest is None:
        return [subtest.group(1), subtest.group(2), subtest.group(3)]
    else:
        return False

def get_pbp(response, inn_half: int) -> str:
    """
    extracts pbp text from appropriate part of page

    Parameters
    ----------
    response : response
        webpage response from scraper
    inn_half : int
        0: top half of inning
        1: bottom half of inning

    Returns
    -------
    str
        Play by play text
    """
        if inn_half == 0:
        play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][1]/text()").get()
        if not play is None:
            if 'No play' in play:
                play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][1]/text()").get()
        else:
            play = "No Play"

    elif inn_half == 1: #right side for bottom half
        play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][3]/text()").get()
        if play is None:
            play = "No Play"
    play = play.replace('3a', ':').replace(';', ':').replace('a dropped fly', 'an error').replace('a muffed throw', 'an error') #replace with input if both out at first and fielders choice
    if 'out at first' in play and 'fielder\'s choice' in play:
        play = input('Enter corrected play text: ')
    return play

def get_lineups(inn_half, lineups):
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
        if not play is None:
            order = lineups[5]
            lineup = lineups[3]
    elif inn_half == 1:
        if not play is None:
            order = lineups[2]
            lineup = lineups[0]
    return [order, lineup]


if 'Dropped foul ball' in play: #need to change this for errors
    play = 'No Play'
    skip = True
# play = play.replace('for WILLIAMS, C.', '.')
#2/15
if 'Allen out at second c to 2b.' in play:
    play = 'Allen out at second c to 2b, caught stealing.'
if 'D LaManna to c for E Copeland' in play:
    play = 'D LaManna to c for Zyska'
#2/16
# if 'HIBBITS pinch ran for SCHROEDER.' in play:
#     play = 'HIBBITS pinch hit for SCHROEDER.'
# if 'FIELDS,J. to rf' in play:
#     play = 'Winikur to rf'

def event_type(s):
    pass

def bat_parse(s, batter):
    pass

def run_parse(s, runners):
    pass

def advance_runners(runners):
    pass

def def_parse(s):
    pass

def compile():
    pass

def reset():
    return [inning, inn_half, outs, runners, play]

def parse_play(plays: list, lineups: list):
    pass

def parse_pbp(inn, line, output, inn_outs):
    event_outs = 0 #keeping track of outs to know if left or right column contains the next play
    outs = inn_outs%3
    pbp_text = get_pbp(response, inn_half)
    sub = is_sub(pbp_txt)
    if sub:
        batter_event_fl = False

    else:
        play_list = pbp_text.split(":")
        parse_play(play_list, lineups)

    for

    return play_info
    ###############PARSE PLAY###################

batter = lineup['name'].iloc[order-1]

        #BAT_ID
        runners[0] = batter
        print('batter: ' + batter + '\nrunners: ' + str(runners) + '\n' + play)
        batter_pos = lineup['position'].iloc[order-1] #find in lineup

        if batter_pos == 'PH':
            ph_fl = True
        else:
            ph_fl = False

        pitches = re.search(r'\(.+?\)', play)
        if pitches is not None:
            pitches = pitches.group()
        else:
            pitches = ''

        # STRIKES_CT
        strikes = re.search(r'(?<=-)[0-2]', pitches)
        if strikes is not None:
            strikes = strikes.group()

        # BALLS_CT
        balls = re.search(r'[0-3](?=-)', pitches)
        if balls is not None:
            balls = balls.group()

        # PITCH_SEQ_TX -- if in play add x
        seq = re.search(r'[A-Z]*(?=\))', pitches)
        if seq is not None:
            seq = seq.group()

        # PIT_ID -- current pitcher in the game for other teams
        if (inn_half == 0):
            pitcher = home_lineup[home_lineup['position'] == 'P'].iloc[0]['name']
            #home team pitcher
            pos2_id = home_lineup[home_lineup['position'] == 'C'].iloc[0]['name']
            pos3_id = home_lineup[home_lineup['position'] == '1B'].iloc[0]['name']
            pos4_id = home_lineup[home_lineup['position'] == '2B'].iloc[0]['name']
            pos5_id = home_lineup[home_lineup['position'] == '3B'].iloc[0]['name']
            pos6_id = home_lineup[home_lineup['position'] == 'SS'].iloc[0]['name']
            pos7_id = home_lineup[home_lineup['position'] == 'LF'].iloc[0]['name']
            pos8_id = home_lineup[home_lineup['position'] == 'CF'].iloc[0]['name']
            pos9_id = home_lineup[home_lineup['position'] == 'RF'].iloc[0]['name']
        else:
            pitcher = away_lineup[away_lineup['position'] == 'P'].iloc[0]['name']
            #away team pitcher
            pos2_id = away_lineup[away_lineup['position'] == 'C'].iloc[0]['name']
            pos3_id = away_lineup[away_lineup['position'] == '1B'].iloc[0]['name']
            pos4_id = away_lineup[away_lineup['position'] == '2B'].iloc[0]['name']
            pos5_id = away_lineup[away_lineup['position'] == '3B'].iloc[0]['name']
            pos6_id = away_lineup[away_lineup['position'] == 'SS'].iloc[0]['name']
            pos7_id = away_lineup[away_lineup['position'] == 'LF'].iloc[0]['name']
            pos8_id = away_lineup[away_lineup['position'] == 'CF'].iloc[0]['name']
            pos9_id = away_lineup[away_lineup['position'] == 'RF'].iloc[0]['name']

        # PIT_HAND_CD -- from roster

        #Runners from stored to output
        run_1st = runners[1] #NEED TO SPECIFY RESPONSIBLE PITCHER
        run_2nd = runners[2]
        run_3rd = runners[3]

        # RESP_PIT_ID
        # RESP_PIT_HAND_CD

        print("battertxt: " + event_txt)
        print("runnertxt: " + str(runners_txt))

        # EVENT_TX
        if 'balk' in play:
            play = play.replace('advanced to second:', 'advanced to second on a balk')
            play = play.replace('advanced to third', 'advanced to third on a balk')

        if 'caught stealing, picked off' in play:
            play = play.replace(', picked off','')

        if 'caught stealing' in play and 'stole' in play:
            play = play.replace('stole', '')

        if 'caught stealing' in play and 'advanced' in play and inn_outs%3 == 2:
            play.replace('advanced to', '')

        event = re.search(r'([sdth][a-z]{3}[rl]ed *((to [a-z]* *[a-z]*)*|(up [a-z]* [a-z]*)|(down [a-z]* [a-z]* [a-z]* *[a-z]*)|(through [a-z]* [a-z]* [a-z]*)))|([a-z]*ed out( to [0-9a-z]{1,2})*)|(popped up( to [0-9a-z]{1,2}))|(infield fly( to [0-9a-z]{1,2}))|(?<!, )out at first|(struck out *[a-z]*)|(reached[ on]*.*((error by [0-9a-z]{1,2})|fielder\'s choice))|reached on catcher\'s interference|walked|(hit by pitch)|((\w* into \w* play ([0-9a-z]{1,2})*)( to [0-9a-z]{1,2})*)|(out on batter\'s interference)', play)
        if not event is None:
            event = event.group()
            print('event: ' + event)
        else:
            event = ''

        run_event = re.search(r'stole [a-z]*|advanced to \w* on (?:a )*(wild pitch|passed ball|balk|defensive indifference)|advanced to \w* on an error by p, failed pickoff attempt|scored on (?:a )*(wild pitch|passed ball|balk|defensive indifference)|out at .*(picked off|caught stealing)', play)
        if not run_event is None:
            print("RUN EVENT")
            run_event = run_event.group()
            run_short_event = re.search(r'stole|wild pitch|passed ball|balk|defensive indifference|picked off|caught stealing|error', run_event).group()
            runner_event_fl = True
            bat_event_test = re.search(r'stole [a-z]*|advanced to \w* on (?:a )*(wild pitch|passed ball|balk|defensive indifference)|advanced to \w* on an error by p, failed pickoff attempt|out at .*(picked off|caught stealing)', event_txt)
            if runners_txt == [] or runners_txt is None:
                runners_txt = [event_txt]
                batter_event_fl = False
                print("runnertxt: " + str(runners_txt))
                print("Batter Event False")
            elif not bat_event_test is None:
                runners_txt = [event_txt] + runners_txt
                print("runnertxt: " + str(runners_txt))
                batter_event_fl = False
                print("Batter Event False")


        if 'error' in event:
            err_type = re.search(r'(?<=a )[a-z]*(?= error)', event)
            if not err_type is None:
                err_type = err_type.group()
            else:
                err_type = 'fielding'
            err_by = (re.search(r'(?<=error by) [0-9a-z]{1,2}', event).group()).upper()
        run_event_abb = ''
        if runner_event_fl:
            if run_short_event in codes:
                run_abb = codes[run_short_event]
                if run_abb in event_codes and event_cd == '':
                    event_cd = event_codes[run_abb]
            if 'wild pitch' in play:
                wp_fl = True
            if 'passed ball' in play:
                pb_fl = True
            print('runner event: ' + run_short_event + '\nevent code: ' + str(event_cd))
        if batter_event_fl:
            short_event = re.search(r'([sdth][a-z]{3}[rl]ed)|([a-z]*ed out)|out at first|popped up|infield fly|(struck out *[a-z]*)|error|(fielder\'s choice)|walked|(hit by pitch)|(\w* into \w* play)|((batter\'s|catcher\'s) interference)', event)
            if not short_event is None and short_event != '':
                short_event = short_event.group()
                print('batter event: ' + short_event)
                if short_event in codes:
                    event_abb = codes[short_event]
                    if event_abb in event_codes:
                        event_cd = event_codes[event_abb]
                        if event_cd in {20,21,22,23}:
                            hit_fl = True
                        if event_cd in {14, 15, 16, 17, 18, 19, 20}:
                            runners_dest[0] = 1
                        if event_cd ==  21:
                            runners_dest[0] = 2
                        if event_cd ==  22:
                            runners_dest[0] = 3
                        if event_cd ==  23:
                            runners_dest[0] = 4
                        print('event code: ' + str(event_cd))
                    else:
                        event_cd = ''
                        print('no event code')
                else:
                     event_abb = ''
            else:
                short_event = ''
            if 'SF' in play:
                sf_fl = True
            if 'SAC' in play:
                sh_fl = True
            if 'bunt' in play:
                bunt_fl = True

            batter_adv = re.search(r'(advanced to [a-z]*)|((scored) on (the throw)|(advanced on an error by [a-z0-9]{1,2}))|(out at [a-z]* [0-9a-z]{1,2}(?: to [0-9a-z]{1,2})*)', event_txt)
            if not batter_adv is None:
                batter_adv = batter_adv.group()
                b_outcome = re.search(r"(advanced to \w*|scored|out at \w*)(?!.*(advanced|scored|out))", batter_adv).group()
            else:
                b_outcome = ''
                batter_adv = ''

        for r in runners_txt:
            runner = re.search(r"^[A-Za-z \'\-,\.]*?(?= (advanced|scored|out|stole))", r)
            if not runner is None:
                runner = runner.group()
            else:
                runner = ''
            if not runner == '':
                runner_outcome = re.search(r"(stole \w*|advanced to \w*|scored|out at \w*)(?!.*(advanced|scored|out))", r)
                if not runner_outcome is None:
                    runner_outcome = runner_outcome.group()
                else:
                    runner_outcome = ''

            if '.' in runner:
                if runner.split('.')[1] == '':
                    runner = runner.replace('.', '')
                elif 'St.' in runner:
                    runner = runner + ','
                else:
                    runner = runner.replace('. ', ' ')
                    runner = runner.replace('.', ' ')
            if ' ' in runner and not ',' in runner:
                if not len(runner.split(' ')[0]) == 1 and not len(runner.split(' ')[1]) > 3:
                    runner = runner.replace(' ', ', ')
            if ',' in runner and not ', ' in runner:
                runner = runner.replace(',', ', ')
            if 'De La ' in runner or 'van ' in runner and not ',' in runner:
                runner = runner + ','
            if ' ' in runner and not ',' in runner:
                runnertemp =  ', ' + runner.split(' ')[0]
                for m in range(1, len(runner.split(' '))):
                    runnertemp = runner.split(' ')[len(runner.split(' '))-m] + ' ' + runnertemp
                runnertemp = runnertemp.replace(' , ', ', ')
                runner = runnertemp

            if not ',' in runner:
                runner = runner + ','

            runnerfull = next((s for s in runners if runner.lower() in s.lower()), None)
            if runnerfull is None:
                runnerfull = next((s for s in runners if runner[0:3].title() in s.title()), None)
            if runnerfull is None:
                runnerfull = ''
            print(runner)
            print(runnerfull)
            print(runners)
            if 'advanced' in runner_outcome:
                runners_dest[runners.index(runnerfull)] = base_codes[re.search(r'(?<=advanced to )\w*', runner_outcome).group()]
            elif 'scored' in runner_outcome:
                runners_dest[runners.index(runnerfull)] = 4
            elif 'stole' in runner_outcome:
                runners_dest[runners.index(runnerfull)] = base_codes[re.search(r'(?<=stole )\w*', runner_outcome).group()]
                run_event_abb = run_event_abb + '/' + str(base_codes[re.search(r'(?<=stole )\w*', runner_outcome).group()])
            else:
                runners_dest[runners.index(runnerfull)] = 0

        if event_cd in {2,3,14,15,16,17,18,19,20,21,22,23}:
             batter_event_fl = True
        if event_cd in range(1,25):
            event_fl = True
        if event_cd in {2,3,18,19,20,21,22,23}:
            ab_fl = True
        if event_cd in {20,21,22,23}:
            hit_fl = True
        if event_cd == 3:
            if 'reached first' in event_txt:
                runners_dest[0] = 1
        elif event_cd in {14, 15, 16, 17, 18, 19, 20}:
            runners_dest[0] = 1
        elif event_cd ==  21:
            runners_dest[0] = 2
        elif event_cd ==  22:
            runners_dest[0] = 3
        elif event_cd ==  23:
            runners_dest[0] = 4
        # elif event_cd in {4,5,6,9,10,11}
        elif not batter_event_fl:
            runners_dest[0] = 5
        else:
            runners_dest[0] = 0
        if batter_event_fl:
            if 'advanced' in b_outcome:
                runners_dest[0] = base_codes[re.search(r'(?<=advanced to )\w*', b_outcome).group()]
            if 'out at' in b_outcome:
                runners_dest[0] = 0
            elif 'scored' in b_outcome:
                runners_dest[0] = 4
        temprunners = ['','','','']
        for base in range(0,4):
            br = runners[3-base]
            if  br != '':
                if runners_dest[3-base] == '':
                    runners_dest[3-base] = 3-base
                dest = runners_dest[3-base]
                if dest > 0 and dest < 4:
                    temprunners[dest] = br
                if dest != 3-base and dest != 5:
                    temprunners[3-base] = ''
                    runners[3-base] = ''
                if dest == 4:
                    if inn_half == 0:
                        away_score += 1
                    else:
                        home_score += 1
                if dest == 0:
                    inn_outs += 1
                    event_outs += 1
        print(runners_dest)
        runners = temprunners


        fld_cd = '' #todo
        bb_cd = '' #do hit descriptions mean ld/fb (eg 'down the -- line, etc? if not, synergy column')
        # fielder  = re.search(r'to [a-z]{1,2}', play).group()
        # event_type = codes[event]
        # event_fl = True



        if event_cd == 2:
            out_location = re.search(r'(?<=out to )[0-9a-z]{1,2}', event)
            if not out_location is None:
                out_location = out_location.group()

        event = event.replace(', RBI', '1 RBI')
        rbi = re.search(r'[1-4]*(?= RBI)', event)
        if rbi is not None:
            rbi = rbi.group()

        if player == '':
            batter_event_fl = False
        if batter_event_fl:
            print('batter: ' + player + ' should be: ' + batter)
            order += 1
            if order == 10:
                order = 1
        if inn_half == 0:
            store_aw_order = order
        else:
            store_hm_order = order
        if batter_event_fl or runner_event_fl:
            event_no += 1

        if inn_outs == 3 and inn_half == 0:
            inn_half = 1
            runners = ['','','','']
            leadoff_fl = True
        elif inn_outs == 6:
            end = True
        else:
            leadoff_fl = False

        if event_outs == 2:
            dp_fl = True
        if event_outs == 3:
            tp_fl = True

        errors = re.findall(r'\w* error by [a-z]{1,2}', play)


        print('event outs: ' + str(event_outs))
        print('event cd: ' + str(event_cd))
        print('inning outs: ' + str(inn_outs))
        playout = [date, home_abb, away_abb, inning, inn_half, outs, balls, strikes, seq, away_score, home_score, batter, pitcher,
        pos2_id, pos3_id, pos4_id, pos5_id, pos6_id, pos7_id, pos8_id, pos9_id,
        run_1st, run_2nd, run_3rd, event_abb, leadoff_fl, ph_fl, batter_pos, order, event_cd,
        batter_event_fl, ab_fl, hit_fl, sh_fl, sf_fl, event_outs, dp_fl, tp_fl,
        rbi, wp_fl, pb_fl, fld_cd, bunt_fl, runners_dest[0], runners_dest[1], runners_dest[2], runners_dest[3], run1_sb, run2_sb, run3_sb, run1_cs, run2_cs, run3_cs, run1_pk, run2_pk, run3_pk, pr1, pr2, pr3, event_no, play]
        print('\n\n')
        if event_fl:
            play_info.append(playout)



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
                callback = self.parse,
                endpoint='render.html',
                args={'wait': .1},
            )

    def parse(self, response):
        links = response.xpath("//div[@id='contentarea']/table/tbody/tr/td[1]/a[@class='skipMask']/@href").getall()
        for link in links:
            abs_url = response.urljoin(link)
            yield SplashRequest(
                url = abs_url,
                callback = self.boxcheck,
                endpoint='render.html',
                args={'wait': .05}
                )

    def boxcheck(self, response):
        box = response.xpath("//div[@id='primary_nav_wrap']/ul[@id='root']/li[1]/a/@href").get()
        boxurl = response.urljoin(box)
        yield SplashRequest(
            url = boxurl,
            callback = self.lineups,
            endpoint = 'render.html',
            args = {'wait':.05}
        )

    def lineups(self, response):
        home_lineup = lineups(home, response)[0]
        away_lineup = lineups(away, response)[0]
        home_subs = lineups(home, response)[1]
        away_subs = lineups(away, response)[1]

        yield SplashRequest(
                url = response.urljoin(response.xpath("//ul[@id='root']/li[3]/a/@href").get()),
                callback = self.parsegame,
                endpoint = 'render.html',
                args = {'wait':.1},
                meta={"away_lineup": away_lineup, "home_lineup": home_lineup, "away_subs": away_subs, "home_subs": home_subs}
                )

    def parsegame(self, response):
        #collects lineups from pbp step
        away_lineup = response.meta["away_lineup"]
        home_lineup = response.meta["home_lineup"]
        home_subs = response.meta["home_subs"]
        away_subs = response.meta["away_subs"]
        play_info = []
        away_score = 0
        home_score = 0

        store_home_order = 1
        store_away_order = 1

        ###GAME INFO###
        innings = response.xpath("//tr[@class='heading']/td[1]/a/text()").getall()[-1] #last listed inning
        last = innings[0:len(innings)-9] #numeric value for last listed inning
        away = response.xpath("//table[@class='mytable'][1]/tbody/tr[2]/td[1]/a/text()").get() #away team
        home = response.xpath("//table[@class='mytable'][1]/tbody/tr[3]/td[1]/a/text()").get() #home team
        date = response.xpath("//div[@id='contentarea']/table[3]/tbody/tr[1]/td[2]/text()").get()[9:19]
        date = date.replace('/', '')
        if len(teamindex[teamindex['school'] == home]) < 1:
            home_abb = home
        else:
            home_abb = teamindex[teamindex['school'] == home].iloc[0]['abbreviation']
        #AWAY_TEAM_ID
        if len(teamindex[teamindex['school'] == away]) < 1:
            away_abb = away
        else:
            away_abb = teamindex[teamindex['school'] == away].iloc[0]['abbreviation']
        ####debug
        print(date + away_abb + ' @ ' + home_abb)
        print(home_lineup)
        print(home_subs)
        print(away_lineup)
        print(away_subs)
        gameid = date + '-' + away_abb + '-' + home_abb

        ###LOOP THROUGH INNINGS###
        n=0 #event number
        event_no = 0
        for inn in range(1, int(last)+1): #loop through each inning
            print("****INNING " + str(inn) + "******")
            inn_outs = 0
            inning = inn
            leadoff_fl = True
            outs = 0
            end = False
            inn_half = 0
            line = 1 #line 2 is first play
            runners = ['','','','']

            ###LOOP THROUGH PLAYS FOR EACH INNING###
            while not end:
                hit_fl = False
                ab_fl = False
                batter_event_fl = True
                runner_event_fl = False
                event_fl = False
                event_abb = ''
                event_cd = ''
                wp_fl = False
                pb_fl = False
                sh_fl = False
                sf_fl = False
                event_outs = 0
                dp_fl = False
                tp_fl = False
                bunt_fl = False
                run_abb = ''
                run_short_event = ''
                runner_outcome = ''
                short_event = ''
                run1_sb = False
                run2_sb = False
                run3_sb = False
                run1_cs = False
                run2_cs = False
                run3_cs = False
                run1_pk = False
                run2_pk = False
                run3_pk = False
                pr1 = False
                pr2 = False
                pr3 = False
                runners_dest = ['','','','']
                skip = False
                sub_name = ''
                subout = ''
                subfull = ''
                outfull = ''
                pos = ''
                line += 1 #go to next play


                parse_play(inn, line, play_info)

                if play == "No Play": #end inning once 6 outs
                    break

        df=pd.DataFrame(play_info, columns=['GameID', 'HomeID', 'AwayID', 'Inning', 'inn_half', 'outs', 'balls', 'strikes', 'seq', 'away_score', 'home_score', 'batter', 'pitcher',
        'pos2_id', 'pos3_id', 'pos4_id', 'pos5_id', 'pos6_id', 'pos7_id', 'pos8_id', 'pos9_id',
        'run_1st', 'run_2nd', 'run_3rd', 'event_abb', 'leadoff_fl', 'ph_fl', 'batter_pos', 'order', 'event_cd',
        'batter_event_fl', 'ab_fl', 'hit_fl', 'sh_fl', 'sf_fl', 'event_outs', 'dp_fl', 'tp_fl',
        'rbi', 'wp_fl', 'pb_fl', 'fld_cd', 'bunt_fl', 'batter_dest', 'runner1_dest', 'runner2_dest', 'runner3_dest', 'run1_sb', 'run2_sb', 'run3_sb', 'run1_cs', 'run2_cs', 'run3_cs', 'run1_pk', 'run2_pk', 'run3_pk', 'pr1', 'pr2', 'pr3', 'event_no', 'pbptext']
)
        df.to_csv('.././pbp/' + date +'.csv', mode='a', index=False, header=False)




#game_id
#home_abb
#home_id
#away_abb
#away_id
#inning
#inn_half
#outs
#balls
#strikes
#pitch_seq
#away_score
#home_score
#batter
#batter_id
#bat_hand
#resp_bat_id
#resp_bat_hand
# PIT_ID
# PIT_HAND_CD
# RESP_PIT_ID
# RESP_PIT_HAND_CD
# POS2_FLD_ID
# POS3_FLD_ID
# POS4_FLD_ID
# POS5_FLD_ID
# POS6_FLD_ID
# POS7_FLD_ID
# POS8_FLD_ID
# POS9_FLD_ID
# BASE1_RUN_ID
# BASE2_RUN_ID
# BASE3_RUN_ID
# EVENT_TX
# LEADOFF_FL
# PH_FL
# BAT_FLD_CD
# BAT_LINEUP_ID
# EVENT_CD
# BAT_EVENT_FL
# AB_FL
# H_FL
# SH_FL
# SF_FL
# EVENT_OUTS_CT
# DP_FL
# TP_FL
# RBI_CT
# WP_FL
# PB_FL
# FLD_CD
# BATTEDBALL_CD
# BUNT_FL
# FOUL_FL
# BATTEDBALL_LOC_TX
# ERR_CT
# ERR1_FLD_CD
# ERR1_CD
# ERR2_FLD_CD
# ERR2_CD
# ERR3_FLD_CD
# ERR3_CD
# BAT_DEST_ID
# RUN1_DEST_ID
# RUN2_DEST_ID
# RUN3_DEST_ID
# BAT_PLAY_TX
# RUN1_PLAY_TX
# RUN2_PLAY_TX
# RUN3_PLAY_TX
# RUN1_SB_FL
# RUN2_SB_FL
# RUN3_SB_FL
# RUN1_CS_FL
# RUN2_CS_FL
# RUN3_CS_FL
# RUN1_PK_FL
# RUN2_PK_FL
# RUN3_PK_FL
# RUN1_RESP_PIT_ID
# RUN2_RESP_PIT_ID
# RUN3_RESP_PIT_ID
# GAME_temp_FL
# GAME_END_FL
# PR_RUN1_FL
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
# ASS5_FLD_CD
# EVENT_ID
