import re
from datetime import date, datetime, timedelta

import lxml.html as lh
import pandas as pd
import requests

teams = pd.read_csv('data/team_ids.csv', index_col = False)
seasons = pd.read_csv('data/seasons.csv', index_col = False)

def get_table(url) -> list:
    """returns a table from a given url

    :param url: website url
    :type url: str
    :return: all tr elements from webpage
    :rtype: list
    """
    return lh.fromstring(requests.get(url).content).xpath('//tr')

def get_lu_table(id) -> list:
    """given a game id returns a list of players and positions for each team

    :param id: game id from ncaa stats webpage
    :type id: int
    :return: list of two lists, for players and positions, separated by team
    :rtype: list
    """
    players = []
    positions = []
    player_id = []
    team_spl = 0

    #Get lineups from situational stats (ss) and box score (bs) pages
    ss_lineups = lh.fromstring(requests.get('https://stats.ncaa.org/game/situational_stats/' + str(id)).content).xpath("//table[@class='mytable'][2]/tr/td[1]")
    bs = lh.fromstring(requests.get('https://stats.ncaa.org/game/box_score/' + str(id)).content)
    bs_a_lineup = bs.xpath("//table[@class='mytable'][2]/tr/td[1]")
    bs_a_pos = bs.xpath("//table[@class='mytable'][2]/tr/td[2]")
    bs_h_lineup = bs.xpath("//table[@class='mytable'][3]/tr/td[1]")
    bs_h_pos = bs.xpath("//table[@class='mytable'][3]/tr/td[2]")

    ss_order = [td[0].text.replace(' Totals', '') for td in ss_lineups if len(td) == 1]
    bs_order = [bs_a_lineup[0].text[0:-1], bs_h_lineup[0].text[0:-1]]

    #If the teams are in the wrong order, switch them
    if ss_order[0] != bs_order[0] and ss_order[1] != bs_order[1]:
        flip = True
    else:
        flip = False

    for i in range(2, len(ss_lineups)-1):
        if ss_lineups[i].text is None and team_spl == 0:
            team_spl = i
        else:
            text = ss_lineups[i].text.split(', ')
            if text[1][-1] == ' ':
                text[1] = text[1][0:-1]
            if 'Jr.' in text[1]:
                players.append(text[0] + ', ' + text[1] + ', ' + text[2])
                positions.append(text[3].split('/'))
            else:
                players.append(text[0] + ', ' + text[1])
                positions.append(text[2].split('/'))            

    if flip:
        players = players[team_spl-2:] + players[0:team_spl-2]
        positions = positions[team_spl-2:] + positions[0:team_spl-2]
        team_spl = len(positions) - team_spl + 4

    #separate home and away players
    for i in range(1, len(bs_a_lineup)-1):
        if bs_a_lineup[i][0].text[-1] == ' ':
            bs_a_lineup[i][0].text = bs_a_lineup[i][0].text[0:-1]
    for i in range(1, len(bs_h_lineup)-1):
        if bs_h_lineup[i][0].text[-1] == ' ':
            bs_h_lineup[i][0].text = bs_h_lineup[i][0].text[0:-1]

    bs_a_players = [bs_a_lineup[i][0].text for i in range(1, len(bs_a_lineup)-1)]
    bs_h_players = [bs_h_lineup[i][0].text for i in range(1, len(bs_h_lineup)-1)]
    ids = {bs_a_lineup[i][0].text:bs_a_lineup[i][0].attrib['href'].split('stats_player_seq=')[-1] for i in range(1, len(bs_a_lineup)-1)}
    ids.update({bs_h_lineup[i][0].text:bs_h_lineup[i][0].attrib['href'].split('stats_player_seq=')[-1] for i in range(1, len(bs_h_lineup)-1)})

    #check number of players on each team
    if len(players[0:team_spl-2]) < len(bs_a_players):
        players = bs_a_players + players[team_spl-2:]
        positions = [bs_a_pos[i].text.lower().split('/') for i in range(0, len(bs_a_pos)-1)] + positions[team_spl-2:]
        team_spl = len(bs_a_players)+2

    if len(players[team_spl-2:]) < len(bs_h_players):
        players = players[0:team_spl-2] + bs_h_players
        positions = positions[0:team_spl-2] + [bs_h_pos[i].text.lower().split('/') for i in range(0, len(bs_h_pos)-1)]

    for i in range(0, len(players)):
        if players[i] in ids.keys():
            player_id.append(ids[players[i]])
        else:
            player_id.append('x' + str(i))
        players[i] = players[i].replace('ñ', 'n')
        positions[i] = [pos.replace('dp', 'dh') for pos in positions[i]] # https://stats.ncaa.org/game/box_score/4937004
   
    return [[players[0:team_spl-2], players[team_spl-2:]], [positions[0:team_spl-2], positions[team_spl-2:]], [player_id[0:team_spl-2], player_id[team_spl-2:]]]
    #TODO: Use positions to help with substitutions

def get_scoreboard(date):
    """gets scoreboard (teams, game ids, and urls) given a date (MM-DD-YYYY)

    :param date: date in format MM-DD-YYYY
    :type date: str
    :return:
    :rtype: [type]
    """
    day = date.split('-')
    url = 'https://stats.ncaa.org/season_divisions/' + str(seasons.loc[seasons['season'] == int(day[2]),'id'].item()) + '/scoreboards?utf8=%E2%9C%93&game_date='+ day[0] +'%2F'+ day[1] + '%2F' + day[2]
    # url = "https://stats.ncaa.org/season_divisions/17126/scoreboards?utf8=%E2%9C%93&season_division_id=&game_date=02%2F25%2F2020&conference_id=0&tournament_id=&commit=Submit"
    page = requests.get(url)
    doc = lh.fromstring(page.content)
    matchups = []
    game = []
    ids = []
    away = []
    home = []
    links = []

    #get elements in td index 3 (away team names and home final scores)
    a_teams = doc.xpath("//div[@id='contentarea']/table/tbody/tr/td[3]")

    #
    for a in range(len(a_teams)):
        if not 'totalcol' in [x for x in a_teams[a].classes]:
            away.append(a_teams[a][0].text if not len(a_teams[a]) < 1 else a_teams[a].text.replace('\n', '').replace('               ', '').replace('            ', ''))

    #get elements in td index 2 (away team logos, home team names and blank element below attendance)
    h_teams = doc.xpath("//div[@id='contentarea']/table/tbody/tr/td[2]")
    for h in range(len(h_teams)):
        if not 'img' in [a.tag for a in h_teams[h]]:
            if not len([a.text for a in h_teams[h]]) > 0:
                test = h_teams[h].text
                if not test is None:
                    team = h_teams[h].text.replace('\n', '').replace('               ', '').replace('            ', '')
                    if not team == '':
                        home.append(team)
            else:
                home.append(h_teams[h][0].text)

    l = doc.xpath("//div[@id='contentarea']/table/tbody/tr/td[1]")
    na = []
    for i in range(round(len(l)/3)):
        e = l[(i)*3+2]
        if len(e) == 0:
            na.append(i)
        else:
            links.append(e[0].attrib['href'])

    deleted = 0
    for i in na:
        del away[i-deleted]
        del home[i-deleted]
        deleted += 1



    # Remove rankings and leading spaces
    for i in range(0,len(away)):
        if '#' in away[i]:
            away[i] = away[i][away[i].index(' ')+1:]
        else:
            away[i] = away[i][1:]

        if '#' in home[i]:
            home[i] = home[i][home[i].index(' ')+1:]
        else:
            home[i] = home[i][1:]
        # Check for doubleheaders
        print(away[i])
        print(home[i])
        m = away[i] + ' ' + home[i]
        if m in matchups:
            game[matchups.index(m)] = 1
            game.append(2)
        else:
            game.append(0)
        matchups.append(m)

    for j in range(len(away)):
        # Remove records
        record_check = re.search(r'([0-9]{1,2}-[0-9]{1,2})', home[j])
        if not record_check is None:
            home[j] = home[j].replace(' (' + home[j].split(' (')[-1], '')
            away[j] = away[j].replace(' (' + away[j].split(' (')[-1], '')
        # Search for team ids
        if len(teams.loc[teams['institution'] == home[j]]) < 1:
            print("ERROR TEAM: " + home[j])
        if len(teams.loc[teams['institution'] == away[j]]) < 1:
            print("ERROR TEAM: " + away[j])
        ids.append(day[2] + day[0] + day[1] + "{:0>6d}".format(teams.loc[teams['institution'] == away[j]]['id'].item()) + "{:0>6d}".format(teams.loc[teams['institution'] == home[j]]['id'].item()) + str(game[j]))
    return pd.DataFrame({'away': away, 'home': home, 'game': game, 'link': links, 'id': ids})

def get_team_schedule(url):
    """Given team page url, scrape list of links to games

    :param url: team page
    :type url: str
    :return: list of links to box scores
    :rtype: list
    """
    page = requests.get(url)
    doc = lh.fromstring(page.content)
    return doc.xpath("//a[@target='BOX_SCORE_WINDOW']/@href")

def get_id(url):
    """takes box score link and returns link to game id used to construct pbp url

    :param url: box score link
    :type url: str
    :return: game id
    :rtype: str
    """
    pages = lh.fromstring(requests.get(url).content).xpath("//ul[@id='root']/li/a/@href")
    return pages[0].split('/')[-1]

#return game info from box score
def get_game_info(id):
    url = 'https://stats.ncaa.org/game/box_score/' + str(id)
    away = lh.fromstring(requests.get(url).content).xpath("//tr[2]/td[1]/a[@class='skipMask']/text()")[0]
    if away[0] == ' ':
        away = away[1:]
    home = lh.fromstring(requests.get(url).content).xpath("//tr[3]/td[1]/a[@class='skipMask']/text()")[0]
    if home[0] == ' ':
        home = home[1:]

    # lh.parse('https://stats.ncaa.org/game/box_score/4705496').xpath("//table[@align='center']/tbody/tr/td")

    # print(lh.tostring(lh.fromstring(requests.get('https://stats.ncaa.org/game/box_score/4705496').content)))
#     info1 = lh.fromstring(requests.get(url).content).xpath("//table")
#     for i in info1:
#         print(i)
#         for e in i:
#             print(e)
#             for a in e:
#                 print(a)
#     info2 = lh.fromstring(requests.get(url).content).xpath("//div[@id='contentarea']/table[3]/tbody/tr/td/text()")
#     info3 = lh.fromstring(requests.get(url).content).xpath("//div[@id='contentarea']/table[4]/tbody/tr/td/text()")
