# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 20:21:10 2019

@author: Miles Okamoto

@todo:
-move runners based on events and additional text
-change player names to player IDs
-responsible runners for pitchers
-organize into methods
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
'CINT': 17,
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

class PbpspiderSpider(scrapy.Spider):
    name = 'pbpspider'
    allowed_domains = ["stats.ncaa.org"]
    start_urls = ['http://csvfeed/']

    def start_requests(self):
        urls = []
        d = date(2019, 2, 15)
        d = str(d)
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
        home_subs = []
        away_subs = []
        home_lineup = pd.DataFrame()
        away_lineup = pd.DataFrame()

        #2 and 3 represent elements for away and home lineups
        for j in {2,3}:
            end = False
            lineup = []
            i = 1
            order = 1

            while not end:
                pitcher = ''
                testname = response.xpath("//table[@class='mytable']["+str(j)+"]/tbody/tr[@class='smtext'][" + str(i) + "]/td[1]/a/text()").get()
                if testname is None: #would happen if it's not a link
                    testname = response.xpath("//table[@class='mytable']["+str(j)+"]/tbody/tr[@class='smtext'][" + str(i) + "]/td[1]/text()").get()
                if not testname is None and not testname == 'Totals' :
                    testname = testname.replace('\xa0', ' ') #replaces spaces in name field

                    #for starting players
                    if not "     " in testname: #filters out subs
                        name = testname.replace('\n', '') #remove new line character
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
                        if j == 2:
                            away_subs.append(name)
                        else:
                            home_subs.append(name)

                else:
                    end = True
            if j == 2:
                away_lineup = pd.DataFrame(lineup, columns = ['order', 'name', 'position'])
            else:
                home_lineup = pd.DataFrame(lineup, columns = ['order', 'name', 'position'])

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
        print(away_lineup)
        print(home_lineup)

        store_hm_order = 1
        store_aw_order = 1

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
        print("START INNING")
        n=0 #event number
        event_no = 0
        for inn in range(1, int(last)+1): #loop through each inning
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
                print('outs: ' + str(inn_outs))
                hit_fl = False
                ab_fl = False
                batter_event_fl = False
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
                subin = ''
                subout = ''
                subfull = ''
                outfull = ''
                pos = ''

                line += 1 #go to next play
                event_outs = 0 #keeping track of outs to know if left or right column contains the next play
                if inn_half == 0: #left side for top half]
                    play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][1]/text()").get()
                    if not play is None:
                        if 'No play' in play:
                            line += 1
                            play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][1]/text()").get()
                    if not play is None:
                        order = store_aw_order
                        lineup = away_lineup
                        # BAT_HOME_ID (1 or 0 for home or away)
                    else:
                        play = "No Play"
                        end = True

                elif inn_half == 1: #right side for bottom half
                    play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][3]/text()").get()
                    if not play is None:
                        if 'No play' in play:
                            line += 1
                            play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][3]/text()").get()
                    if not play is None:
                        order = store_hm_order
                        lineup = home_lineup
                    else:
                        play = "No Play"
                        end = True
                if end: #end inning once 6 outs
                    break
                # OUTS_CT
                outs = inn_outs%3
                play = play.replace('3a', ':')
                play = play.replace(';', ':')
                play = play.replace('a dropped fly', 'an error')
                play = play.replace('a muffed throw', 'an error')
                play = play.replace('out at first ss to 2b, reached on a fielder\'s choice', ' reached on a fielder\'s choice')


                # play = play.replace('for WILLIAMS, C.', '.')



                if 'Popup' in play:
                    skip = True
                if 'Umpires review' in play:
                    skip = True
                if 'Hamrock, D. pinch ran for Richardson.' in play:
                    play = 'Hamrock, D. pinch ran for Weiller, J..'
                event_txt = play.split(":")[0]
                runners_txt = play.split(": ")[1:]

                player = re.search(r'(?:(?:[a-z]* (?![a-z]))*[A-Z][A-Za-z\'\.\,-]*)*', event_txt)
                if not player is None:
                    player = player.group() #this used more to filter out -use lineups to id batters

                #########TEST IF PLAY IS SUBSTITUTION##########
                subtest = re.search(r"(?:(?:[a-z]* (?![a-z]))*[A-Z][A-Za-z'\.\,-]*){1,} (pinch (?:hit|ran)|to [0-9a-z]{1,2}) *(for(?:(?:\.* (?![a-z]))*[A-Z][A-Za-z'\.\,-]*)*)*", event_txt)
                if not subtest is None:
                    sub_txt = subtest.group()
                    print(sub_txt)
                if '/  for' in event_txt:
                    subtest = lu[lu['position']=='P'].iloc[0]['name'] + ' to p' + event_txt.split('/ ')[1]
                     #####IF PH for DH not replaced, they become DH
                elif end:
                    end = True
                elif skip:
                    skip = True
                elif not subtest is None:
                    #pinch hitter/runner
                    if 'pinch' in sub_txt:
                        if inn_half == 0:
                            lu = away_lineup
                            subs = away_subs
                        else:
                            lu = home_lineup
                            subs = home_subs
                        if 'hit' in sub_txt:
                            subin = re.search(r"([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*(?= | [a-z])(?= pinch hit for)", sub_txt).group()
                            subtype = 'off'
                            pos = 'PH'

                        elif 'ran' in sub_txt:
                            subin = re.search(r"([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*(?= | [a-z])(?= pinch ran for)", sub_txt).group()
                            subtype = 'off'
                            pos = 'PR'
                    #Replace DH could be offensive

                    else:
                        subin = re.search(r"([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*(?= | [a-z])(?= to [0-9a-z]{1,2})", sub_txt).group()
                        pos = (re.search(r'(?<= to )[0-9a-z]{1,2}', sub_txt).group()).upper()
                        subtype = 'def'
                        if inn_half == 1:
                            lu = away_lineup
                            subs = away_subs
                        else:
                            lu = home_lineup
                            subs = home_subs
                    #fix formatting to match lineup
                    if '.' in subin:
                        if subin.split('.')[1] == '':
                            subin = subin.replace('.', '')
                        elif 'St.' in subin:
                            subin = subin + ','
                        else:
                            subin = subin.replace('. ', ' ')
                            subin = subin.replace('.', ' ')
                    if ' ' in subin and not ',' in subin:
                        if not len(subin.split(' ')[0]) == 1 and not len(subin.split(' ')[1]) > 3:
                            subin = subin.replace(' ', ', ')
                    if ',' in subin and not ', ' in subin:
                        subin = subin.replace(',', ', ')
                    if 'De La ' in subin or 'van ' in subin and not ',' in subin:
                        subin = subin + ','
                    if ' ' in subin and not ',' in subin:
                        subinnew =  ', ' + subin.split(' ')[0]
                        for m in range(1, len(subin.split(' '))):
                            subinnew = subin.split(' ')[len(subin.split(' '))-m] + ' ' + subinnew
                        subinnew = subinnew.replace(' , ', ', ')
                        subin = subinnew

                    if not ',' in subin:
                        subin = subin + ','

                    #distinguish between positional changes and defensive subs
                    if not ' for ' in sub_txt:
                        sublist = lu['name']
                    else:
                        sublist = lu['name']
                        subfull = next((s for s in sublist if subin.lower() in s.lower()), None)
                        if subfull is None:
                            sublist = subs

                    #check if replacement is in either lineup or subs list
                    subfull = next((s for s in sublist if subin.lower() in s.lower()), None)

                    #if not, try the first 4 letters of the name for a match
                    if subfull is None:
                        subfull = next((s for s in sublist if subin[0:3].title() in s.title()), None)

                    if subfull is None and pos == 'P':
                        sublist = subs
                        subfull = next((s for s in sublist if subin.lower() in s.lower()), None)
                        if subfull is None:
                            subfull = next((s for s in sublist if subin[0:3].title() in s.title()), None)
                        # if not subfull is None:
                        #     if len(lu[lu['order']=='P']) == 0:
                        #         print('adding pitcher')
                        #         lu.loc[10] = ['P', subfull, pos]

                    #if not, then it's actually a sub on the other side (mislabeled pinch hitter usually)
                    if subfull is None:
                        if subtype == 'def':
                            subtype = 'off'
                            ph_fl = True
                            if inn_half == 0:
                                lu = away_lineup
                                subs = away_subs
                            else:
                                lu = home_lineup
                                subs = home_subs
                            if not ' for ' in sub_txt:
                                sublist = lu['name']
                            else:
                                sublist = subs
                            subfull = next((s for s in sublist if subin.lower() in s.lower()), None)
                            if subfull is None:
                                subfull = next((s for s in sublist if subin[0:3].title() in s.title()), None)

                        else:
                            subtype = 'def'
                            if inn_half == 1:
                                lu = away_lineup
                                subs = away_subs
                            else:
                                lu = home_lineup
                                subs = home_subs
                            if not 'for' in sub_txt:
                                sublist = lu['name']
                            else:
                                sublist = subs
                            subfull = next((s for s in sublist if subin.lower() in s.lower()), None)
                            if subfull is None:
                                subfull = next((s for s in sublist if subin[0:3].title() in s.title()), None)

                    #find replaced player
                    if ' for ' in sub_txt:
                        subout = re.search(r"(?<= for )([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*(?=.)", sub_txt).group()
                        #reformat
                        if '.' in subout:
                            if subout.split('.')[1] == '':
                                subout = subout.replace('.', '')
                            elif 'St.' in subin:
                                subin = subin + ','
                            else:
                                subout = subout.replace('. ', ' ')
                                subout = subout.replace('.', ' ')
                        if ' ' in subout and not ',' in subout:
                            if not len(subout.split(' ')[0]) == 1  and not len(subout.split(' ')[1]) > 3:
                                subout = subout.replace(' ', ', ')
                        if ',' in subout and not ', ' in subout:
                            subout = subout.replace(',', ', ')
                        if 'De La ' in subout or 'van ' in subout and not ',' in subout:
                            subout = subout + ','
                        if ' ' in subout and not ',' in subout:
                            suboutnew =  ', ' + subout.split(' ')[0]
                            for m in range(1, len(subout.split(' '))):
                                suboutnew = subout.split(' ')[len(subout.split(' '))-m] + ' ' + suboutnew
                            suboutnew = suboutnew.replace(' , ', ', ')
                            subout = suboutnew

                        if not ',' in subout:
                            subout = subout + ','
                        outfull = next((s for s in lu['name'] if subout.lower() in s.lower()), None)
                        if outfull is None:
                            outfull = next((s for s in lu['name'] if subout[0:3].title() in s.title()), None)
                            if outfull is None:
                                if subtype == 'def':
                                    subtype = 'off'
                                    ph_fl = True
                                    if inn_half == 0:
                                        lu = away_lineup
                                        subs = away_subs
                                    else:
                                        lu = home_lineup
                                        subs = home_subs
                                    outfull = next((s for s in lu['name'] if subout.lower() in s.lower()), None)
                                    if subfull is None:
                                        subfull = next((s for s in sublist if subin[0:3].title() in s.title()), None)
                                else:
                                    subtype = 'def'
                                    if inn_half == 1:
                                        lu = away_lineup
                                        subs= away_subs
                                    else:
                                        lu = home_lineup
                                        subs = home_subs
                                    outfull = next((s for s in lu['name'] if subout.lower() in s.lower()), None)
                                    if subfull is None:
                                        subfull = next((s for s in sublist if subin[0:3].title() in s.title()), None)
                                if subfull is None:
                                    subfull = ''
                                if outfull is None:
                                    outfull = ''
                        print(lu)
                        print(subs)
                        print(subin)
                        print(subfull)
                        print(subout)
                        print(outfull)
                        if len(lu.index[lu['name'] == outfull].tolist()) > 0:
                            print(lu.index[lu['name'] == outfull].tolist()[0])
                            lu.iloc[lu.index[lu['name'] == outfull].tolist()[0]] = [lu.iloc[lu.index[lu['name'] == outfull].tolist()[0]]['order'], subfull, pos]
                        if pos == 'P':
                            lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]] = [lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]]['order'], subfull, pos]
                        print(lu)
                    else:
                        print(lu)
                        print(subin)
                        print(subfull)
                        if pos == 'P':
                            if len(lu[lu['order'] == 'P']['order'].tolist()) == 0:
                                print('adding pitcher')
                                lu.loc[9] = ['P', subfull, pos]
                            else:
                                if len(lu.index[lu['name'] == subfull].tolist()) > 1:
                                    lu = lu.drop([9])
                                    lu.iloc[lu.index[lu['name'] == subfull].tolist()[0]] = [lu.iloc[lu.index[lu['name'] == subfull].tolist()[0]]['order'], subfull, pos]
                                else:
                                    lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]] = [lu.iloc[lu.index[lu['order'] == 'P'].tolist()[0]]['order'], subfull, pos]

                        else:
                            if len(lu.index[lu['name'] == subfull].tolist()) > 0:
                                lu.iloc[lu.index[lu['name'] == subfull].tolist()[0]] = [lu.iloc[lu.index[lu['name'] == subfull].tolist()[0]]['order'], subfull, pos]
                        print(lu)
                    if (inn_half == 0 and subtype == 'off') or (inn_half == 1 and subtype == 'def'):
                        away_lineup = lu
                    else:
                        home_lineup = lu
                    if pos == 'PR':
                        runners[runners.index(outfull)] = subfull



                ###############PARSE PLAY###################
                else:
                    batter = lineup['name'].iloc[order-1]

                    #BAT_ID
                    runners[0] = batter
                    print(play + 'batter: ' + batter + ' //outs: ' + str(inn_outs) + '//runners: ' + str(runners))
                    batter_pos = lineup['position'].iloc[order-1] #find in lineup

                    if batter_pos == 'PH':
                        ph_fl = True
                    else:
                        ph_fl = False

                     #find in lineup
                    # BAT_FLD_CD
                    # BAT_LINEUP_ID
                    # PH_FL - True if pinch hitter, set to false at end of each play IF it's an event for that hitter
                        #do we consider ph if up to bat, caught stealing, comes back up next inning? Ford vs lamar
                        #also we have to put batter up to bat for event but not batter event flag
                    # BAT_HAND_CD - from roster
                    # RESP_BAT_ID - if pinch hit in middle of ab
                    # RESP_BAT_HAND_CD

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


                    # EVENT_TX
                    event = re.search(r'([sdth][a-z]{3}[rl]ed *((to [a-z]* *[a-z]*)*|(up [a-z]* [a-z]*)|(down [a-z]* [a-z]* [a-z]* *[a-z]*)|(through [a-z]* [a-z]* [a-z]*)))|([a-z]*ed out( to [0-9a-z]{1,2})*)|(popped up( to [0-9a-z]{1,2}))|(infield fly( to [0-9a-z]{1,2}))|(?<!, )out at first|(struck out *[a-z]*)|(reached[ on]*.*((error by [0-9a-z]{1,2})|fielder\'s choice))|walked|(hit by pitch)|((\w* into \w* play ([0-9a-z]{1,2})*)( to [0-9a-z]{1,2})*)|(out on batter\'s interference)', play)
                    if not event is None:
                        event = event.group()
                        print('event: ' + event)
                    if 'picked off' in play or 'caught stealing' in play::
                        runner_event_fl = True
                        runners_txt.append(event_txt)
                        # if re.search(r'stole [a-z]*|advanced to \w* on (?:a )*(wild pitch|passed ball|balk|defensive indifference)|out at .*(picked off|caught stealing)', event_txt) is None:
                    if 'error' in event:
                        err_type = re.search(r'(?<=a )[a-z]*(?= error)', event)
                        if not err_type is None:
                            err_type = err_type.group()
                        else:
                            err_type = 'fielding'
                        err_by = (re.search(r'(?<=error by) [0-9a-z]{1,2}', event).group()).upper()

                    if 'SF' in event:
                        sf_fl = True
                    if 'SAC' in event:
                        sh_fl = True
                    if 'bunt' in event:
                        bunt_fl = True

                    run_event_abb = ''
                    if runner_event_fl:
                        run_event = re.search(r'stole [a-z]*|advanced to \w* on (?:a )*(wild pitch|passed ball|balk|defensive indifference)|out at .*(picked off|caught stealing)', event_txt)
                        if not run_event is None:
                            run_event = run_event.group()
                            run_short_event = re.search(r'stole [a-z]*|advanced to \w* on (?:a )*(wild pitch|passed ball|balk|defensive indifference)|out at .*(picked off|caught stealing)', run_event).group(1)
                        if run_short_event in codes:
                            run_abb = codes[run_short_event]
                            if run_abb in event_codes and event_cd == '':
                                event_cd = event_codes[run_abb]
                        if 'wild pitch' in play:
                            wp_fl = True

                        if 'passed ball' in play:
                            pb_fl = True
                    else:
                        short_event = re.search(r'([sdth][a-z]{3}[rl]ed)|([a-z]*ed out)|out at first|popped up|infield fly|(struck out *[a-z]*)|error|(fielder\'s choice)|walked|(hit by pitch)|(\w* into \w* play)|(batter\'s interference)', event)
                    if not short_event is None and short_event != '':
                        short_event = short_event.group()
                    else:
                        short_event = ''
                    if short_event in codes:
                        event_abb = codes[short_event]
                    else:
                         event_abb = ''
                    if event_abb in event_codes:
                        event_cd = event_codes[event_abb]
                    else:
                        event_cd = ''
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

                    batter_adv = re.search(r'(advanced to [a-z]*)|((scored) on (the throw)|(advanced on an error by [a-z0-9]{1,2}))|(out at [a-z]* [0-9a-z]{1,2}(?: to [0-9a-z]{1,2})*)', event_txt)
                    if not batter_adv is None:
                        batter_adv = batter_adv.group()
                        b_outcome = re.search(r"(advanced to \w*|scored|out at \w*)(?!.*(advanced|scored|out))", batter_adv).group()
                    else:
                        b_outcome = ''
                        batter_adv = ''

                    if event_cd in {2,3,14,15,16,17,18,19,20,21,22,23}:
                         batter_event_fl = True
                    if event_cd in range(1,25):
                        event_fl = True
                    if event_cd in {2,3,18,19,20,21,22,23}:
                        ab_fl = True
                    if event_cd in {20,21,22,23}:
                        hit_fl = True

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
                            runnernew =  ', ' + runner.split(' ')[0]
                            for m in range(1, len(runner.split(' '))):
                                runnernew = runner.split(' ')[len(runner.split(' '))-m] + ' ' + runnernew
                            runnernew = runnernew.replace(' , ', ', ')
                            runner = runnernew

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
                    elif event_cd in {4,5,6,9,10,11} or not batter_event_fl:
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
                    newrunners = ['','','','']
                    for base in range(0,4):
                        br = runners[3-base]
                        if  br != '':
                            if runners_dest[3-base] == '':
                                runners_dest[3-base] = 3-base
                            dest = runners_dest[3-base]
                            if dest > 0 and dest < 4:
                                newrunners[dest] = br
                            if dest != 3-base and dest != 5:
                                newrunners[3-base] = ''
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
                    runners = newrunners


                    fld_cd = '' #todo
                    bb_cd = '' #do hit descriptions mean ld/fb (eg 'down the -- line, etc? if not, synergy column')
                    # fielder  = re.search(r'to [a-z]{1,2}', play).group()
                    # event_type = codes[event]
                    # event_fl = True



                    if event_cd == 2:
                        out_location = re.search(r'(?<=out to )[0-9a-z]{1,2}', event)
                        if not out_location is None:
                            out_location = out_location.group()

                    # SH_FL
                    # SF_FL
                    # EVENT_OUTS_CT
                    # DP_FL
                    # TP_FL
                    # RBI_CT
                    event = event.replace(', RBI', '1 RBI')
                    rbi = re.search(r'[1-4]*(?= RBI)', event)
                    if rbi is not None:
                        rbi = rbi.group()
                    # WP_FL
                    # PB_FL
                    # FLD_CD -- 0  if strikeout/walk/hr


                    # BATTEDBALL_CD #G/L/F --- popouts F, sort by fly balls to infielders
                    # BUNT_FL
                    # FOUL_FL
                    # BATTEDBALL_LOC_TX
                    if player == '':
                        batter_event_fl = False
                    if batter_event_fl:
                        print('batter event: True' + 'order = ' + str(order) + 'next = ' + str(order+1))
                        print('batter: ' + player + ' order batter: ' + batter)
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
                    # error_ct = len(errors)
                    # if error_ct >= 1:
                    #     error_1 = errors[1]
                    # if error_ct >= 2:
                    #     error_2 = errors[2]
                    # if error_ct == 3:
                    #     error_3 = errors[3]
                    # error_1_fld = re.search(r'[a-z]{1,2}', error_1).group()
                    # error_2_fld = re.search(r'[a-z]{1,2}', error_2).group()
                    # error_3_fld = re.search(r'[a-z]{1,2}', error_3).group()



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
            # ERR_CT -- fielding or throwing?
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
            # RUN1_PLAY_TX  - this is for a double play or fc
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
            # GAME_NEW_FL
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
            #column at end for full text






            #GameID
            #HomeID
            #AwayID
            #Inning
            #BatterID
            #inn_half
            #outs
            #balls
            #strikes
            # PITCH_SEQ_TX
            # AWAY_SCORE_CT
            # HOME_SCORE_CT
            # BAT_ID
            # BAT_HAND_CD
            # RESP_BAT_ID
            # RESP_BAT_HAND_CD
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
            # GAME_NEW_FL
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


#                    df=pd.DataFrame(play_info,columns=['Date','GameID', 'Team', 'Batter', 'Event', 'RBI', 'Count', 'EventNo', 'AB'])
        df=pd.DataFrame(play_info, columns=['GameID', 'HomeID', 'AwayID', 'Inning', 'inn_half', 'outs', 'balls', 'strikes', 'seq', 'away_score', 'home_score', 'batter', 'pitcher',
        'pos2_id', 'pos3_id', 'pos4_id', 'pos5_id', 'pos6_id', 'pos7_id', 'pos8_id', 'pos9_id',
        'run_1st', 'run_2nd', 'run_3rd', 'event_abb', 'leadoff_fl', 'ph_fl', 'batter_pos', 'order', 'event_cd',
        'batter_event_fl', 'ab_fl', 'hit_fl', 'sh_fl', 'sf_fl', 'event_outs', 'dp_fl', 'tp_fl',
        'rbi', 'wp_fl', 'pb_fl', 'fld_cd', 'bunt_fl', 'batter_dest', 'runner1_dest', 'runner2_dest', 'runner3_dest', 'run1_sb', 'run2_sb', 'run3_sb', 'run1_cs', 'run2_cs', 'run3_cs', 'run1_pk', 'run2_pk', 'run3_pk', 'pr1', 'pr2', 'pr3', 'event_no', 'pbptext']
)
        df.to_csv('.././pbp/' + date +'.csv', mode='a', index=False, header=False)
