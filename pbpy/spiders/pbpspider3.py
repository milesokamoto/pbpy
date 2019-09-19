# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 3:50:09 2019

@author: Miles Okamoto

@todo:
-fix reset play to start over with custom input
-change runners[] if a pinch runner
-eventually index stats.ncaa pbp names to roster names to player ids

-structure: lineup -> y -> parse -> y -> done
                   -> n -> input -> parse -> n -> manual plays

"""
import scrapy
from scrapy_splash import SplashRequest
import pandas as pd
from datetime import timedelta, date #build in script that runs everyday for yesterday
import re
import Levenshtein

teamindex = pd.read_csv('https://raw.githubusercontent.com/milesok/NCAA-Baseball-Analytics/master/data/teams.csv')
codes = {
    'singled': '1B',
    'doubled': '2B',
    'tripled': '3B',
    'homered': 'HR',
    'flied out': 'F',
    'flied into double play': 'F',
    'popped up': 'P',
    'popped out': 'P',
    'infield fly': 'P', #label w/ flag?
    'popped into double play': 'F',
    'lined into double play': 'L',
    'lined into triple play': 'L',
    'lined out': 'L',
    'grounded out': 'G',
    'out at first': 'G', ##ONLY FOR BATTERS - check on this for fielding
    'grounded into double play': 'G',
    'hit into double play': 'G',
    'hit into triple play': 'G',nto double play': 'F',
    'fouled out': 'F', #when doing fielders, add f after fielder code
    'struck out looking': 'KL',
    'struck out swinging': 'KS',
    'struck out': 'K',
    'struck out ': 'K',
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
    try:
        end = False
        lineup = []
        subs = []
        i = 1
        order = 1
        dh = False
        if team == 'away':
            j = 2
        else:
            j = 3
        while not end:
            pitcher = ''
            testname = response.xpath("//table[@class='mytable']["+str(j)+"]/tbody/tr[@class='smtext'][" + str(i) + "]/td[1]/a/text()").get()
            if testname is None: #no player link
                testname = response.xpath("//table[@class='mytable']["+str(j)+"]/tbody/tr[@class='smtext'][" + str(i) + "]/td[1]/text()").get()
            if not testname is None and not testname == 'Totals' :
                testname = testname.replace('\xa0', ' ').replace('ñ', 'n').replace(' ,', ',') #replaces spaces in name field
                if not "     " in testname: #filters out subs
                    name = testname.replace('\n', '') #remove temp line character
                    postxt = response.xpath("//table[@class='mytable']["+str(j)+"]/tbody/tr[@class='smtext'][" + str(i) + "]/td[2]/text()").get()
                    if not postxt is None:
                        pos = postxt.split('/')[0]
                    if 'P' in postxt:
                        subs.append(name)
                    if pos == "DH":
                        lineup.append([order, name, pos])
                        order += 1
                        dh = True
                    elif pos == "P":
                        if order <= 9: #check if pitcher is hitting
                            lineup.append([order, name, pos])
                            order += 1
                        else:
                            lineup.append(['P', name, pos])
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
                else:
                    name = testname.replace('\n', '').replace('     ', '').replace(' ,', ',')
                    i += 1
                    subs.append(name)
            elif order < 10 or (order < 11 and dh):
                full_lu = False
                lineup = []
                subs = []
            else:
                full_lu = True
                end = True
        return [pd.DataFrame(lineup, columns = ['order', 'name', 'position']), subs, full_lu]
    except Exception as ex:
        print(ex)

def get_pbp(response, inn_half: int, inn: int, line: int,last) -> list:
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
            if any([x in play.lower() for x in block]) or 'Left Field:' in play or ('failed pickoff attempt.' in play and not 'advanced' in play) or ('picked off' in play and not 'out at' in play) or play == '.' or play[0] == '(':
                line += 1
                return get_pbp(response, inn_half, inn, line,last)
        else:
            play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][3]/text()").get()
            if not play is None:
              if any([x in play.lower() for x in block]) or 'Left Field:' in play or ('failed pickoff attempt.' in play and not 'advanced' in play) or ('picked off' in play and not 'out at' in play) or play == '.' or play[0] == '(':
                    line += 1
                    return get_pbp(response, inn_half, inn, line,last)
            if play is None:
                play = "No Play"
            else:
                play = "No Play"

    elif inn_half == 1: #right side for bottom half
        play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][3]/text()").get()
        if not play is None:
          if any([x in play.lower() for x in block]) or 'Left Field:' in play or ('failed pickoff attempt.' in play and not 'advanced' in play) or ('picked off' in play and not 'out at' in play) or play == '.' or play[0] == '(':
                line += 1
                return get_pbp(response, inn_half, inn, line,last)
        if play is None:
            play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][1]/text()").get()
            if not play is None:
                if any([x in play.lower() for x in block]) or ('failed pickoff attempt.' in play and not 'advanced' in play) or ('picked off' in play and not 'out at' in play) or play == '.' or play[0] == '(':
                    line += 1
                    return get_pbp(response, inn_half, inn, line,last)
            else:
                play = "No Play"
    if play == 'No Play':
        end = True
    else:
        end = False
    play = play.replace('3a', ':').replace(';', ':').replace('a dropped fly', 'an error').replace('a muffed throw', 'an error') #replace with input if both out at first and fielders choice
    return [play, line, end]

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
        raise NameError("Couldn't find name")

def find_name(name: str, list: list, switched) -> str:
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
    full = next((s for s in list if name.title() in s.title()), None)
    if full is None:
        full = next((s for s in list if name.replace(' Jr', '').replace('.','').title() in s.replace(' Jr.','').title()), None)
    if full is None and len(name.split(',')[0]) > 6:
        full = next((s for s in list if name.split(',')[0][:-2].title() in s.title()), None)
    if full is None and not switched:
        full = 'switch'
    elif full is None:
        raise TypeError('no name found')
    return full



# names = ["Ellis, Duke", "Zubia, Zach", "Henley, Blair"]
#
# namedict = {
#     "Ellis, Duke": "Ellis",
#     "Zubia, Zach": "",
#     "Henley, Blair": "",
# }
#
# name = "Henley, B"
# max = 0
# for full, short in namedict.items():
#     if short == name:
#         print(full)
#     else:
#         ratio = Levenshtein.ratio(name, full)
#         print(full)
#         print(name)
#         print(ratio)
#         print(max)
#         if ratio > max:
#             max = ratio
#             match = full
# namedict[match] = name
#
# Levenshtein.ratio("Zubia", "Henley, Blair")
