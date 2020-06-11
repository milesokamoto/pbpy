import requests
import lxml.html as lh
import pandas as pd
from datetime import date, datetime, timedelta
import re

teams = pd.read_csv('teams.csv', index_col = False)
seasons = pd.read_csv('./seasons.csv', index_col = False)

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

    if ss_order != bs_order:
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
            players.append(text[0] + ', ' + text[1])
            positions.append(text[2].split('/'))

    if flip:
        players = players[team_spl-2:] + players[0:team_spl-2]
        positions = positions[team_spl-2:] + positions[0:team_spl-2]
        team_spl = len(positions) - team_spl + 4

    bs_a_players = [bs_a_lineup[i][0].text for i in range(1, len(bs_a_lineup)-1)]
    bs_h_players = [bs_h_lineup[i][0].text for i in range(1, len(bs_h_lineup)-1)]

    if len(players[0:team_spl-2]) < len(bs_a_players):
        players = bs_a_players + players[team_spl-2:]
        positions = [bs_a_pos[i].text.lower().split('/') for i in range(0, len(bs_a_pos)-1)] + positions[team_spl-2:]
        team_spl = len(bs_a_players)+2

    if len(players[team_spl-2:]) < len(bs_h_players):
        players = players[0:team_spl-2] + bs_h_players
        positions = positions[0:team_spl-2] + [bs_h_pos[i].text.lower().split('/') for i in range(0, len(bs_h_pos)-1)]

    for i in range(0, len(players)):
        players[i] = players[i].replace('ñ', 'n')
        
    return [[players[0:team_spl-2], players[team_spl-2:]], [positions[0:team_spl-2], positions[team_spl-2:]]]
#TODO: Use positions to help with substitutions

#gets scoreboard (teams, game ids, and urls) given a date (MM-DD-YYYY)
def get_scoreboard(date):
    day = date.split('-')
    url = 'https://stats.ncaa.org/season_divisions/' + str(seasons.loc[seasons['season'] == int(day[2]),'id'].item()) + '/scoreboards?utf8=%E2%9C%93&game_date='+ day[0] +'%2F'+ day[1] + '%2F' + day[2]
    page = requests.get(url)
    doc = lh.fromstring(page.content)
    matchups = []
    game = []
    ids = []
    away = []
    home = []
    a_teams = doc.xpath("//div[@id='contentarea']/table/tbody/tr/td[3]")
    for a in range(0, round(len(a_teams)/2)):
        away.append(a_teams[2*a][0].text if not len(a_teams[2*a]) < 1 else a_teams[2*a].text.replace('\n', '').replace('               ', '').replace('            ', ''))
    h_teams = doc.xpath("//div[@id='contentarea']/table/tbody/tr/td[2]")
    for h in range(0, round(len(h_teams)/3)):
        home.append(h_teams[3*h+1][0].text if not len(h_teams[3*h+1]) < 1 else h_teams[3*h+1].text.replace('\n', '').replace('               ', '').replace('            ', ''))
    links = doc.xpath("//div[@id='contentarea']/table/tbody/tr/td[1]/a/@href")

    for i in range(0,len(away)):
        if '#' in away[i]:
            away[i] = away[i].split(' ')[2:]
        else:
            away[i] = away[i][1:]
        if '#' in home[i]:
            home[i] = home[i].split(' ')[2:]
        else:
            home[i] = home[i][1:]
        m = away[i] + ' ' + home[i]
        if m in matchups:
            game[matchups.index(m)] = 1
            game.append(2)
        else:
            game.append(0)
        matchups.append(m)
    for j in range(0,len(away)):
        if len(re.search(r'([0-9]{1,2}-[0-9]{1,2})', home[j]).group()):
            home[j] = home[j].replace(' (' + home[j].split(' (')[-1], '')
            away[j] = away[j].replace(' (' + away[j].split(' (')[-1], '')
        if len(teams.loc[teams['institution'] == home[j]]) < 1:
            print("ERROR TEAM: " + home[j])
        if len(teams.loc[teams['institution'] == away[j]]) < 1:
            print("ERROR TEAM: " + away[j]),
        ids.append(day[2] + day[0] + day[1] + "{:0>6d}".format(teams.loc[teams['institution'] == away[j]]['id'].item()) + "{:0>6d}".format(teams.loc[teams['institution'] == home[j]]['id'].item()) + str(game[j]))
    return pd.DataFrame({'away': away, 'home': home, 'game': game, 'link': links, 'id': ids})

# param: url is team page, returns list of links to box scores
def get_team_schedule(url):
    page = requests.get(url)
    doc = lh.fromstring(page.content)
    return doc.xpath("//a[@target='BOX_SCORE_WINDOW']/@href")

# takes box score link and returns link to game id for pbp
def get_id(url):
    pages = lh.fromstring(requests.get(url).content).xpath("//ul[@id='root']/li/a/@href")
    return pages[0].split('/')[-1]

#return game info from box score
# url = 'https://stats.ncaa.org/game/box_score/4705496'
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