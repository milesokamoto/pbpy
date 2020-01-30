import requests
import lxml.html as lh
import pandas as pd
from datetime import date, datetime, timedelta

teams = pd.read_csv('teams.csv', index_col = False)
seasons = pd.read_csv('../seasons.csv', index_col = False)

#returns a table from a given site
def get_table(url) -> list:
    return lh.fromstring(requests.get(url).content).xpath('//tr')

def get_lu_table(url) -> list:
    players = []
    positions = []
    lineups = lh.fromstring(requests.get(url).content).xpath('//tr[@class="smtext"]/td[1]')
    team_spl = len(lh.fromstring(requests.get(url).content).xpath("//table[@class='mytable'][2]")[0])-3
    for td in lineups:
        players.append(td[0].text if len(td)>0 else td.text.replace('\n', ''))
    pos = lh.fromstring(requests.get(url).content).xpath('//tr[@class="smtext"]/td[2]')
    for td in pos:
        positions.append(td.text)
    return [[players[0:team_spl], players[team_spl:]], [positions[0:team_spl], positions[team_spl:]]]

#gets scoreboard (teams, game ids, and urls) given a date (MM-DD-YYYY)
def get_scoreboard(date):
    day = date.split('-')
    url = 'https://stats.ncaa.org/season_divisions/' + str(seasons.loc[seasons['season'] == int(day[2]),'id'].item()) + '/scoreboards?utf8=%E2%9C%93&game_date='+ day[0] +'%2F'+ day[1] + '%2F' + day[2]

    page = requests.get(url)
    doc = lh.fromstring(page.content)
    matchups = []
    game = []
    ids = []
    away = doc.xpath("//div[@id='contentarea']/table/tbody/tr/td[3]")
    for a in range(0, round(len(away)/2)):
        print(away[2*a][0].text if not len(away[2*a]) < 1 else away[2*a].text.replace('\n', '').replace('               ', ''))
    home = doc.xpath("//div[@id='contentarea']/table/tbody/tr/td[2]/a/text()")
    links = doc.xpath("//div[@id='contentarea']/table/tbody/tr/td[1]/a/@href")
    len(away)
    len(home)
    len(links)
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
        if len(teams.loc[teams['institution'] == home[j]]) < 1:
            print("ERROR TEAM: " + home[j])
        if len(teams.loc[teams['institution'] == away[j]]) < 1:
            print("ERROR TEAM: " + away[j])
        ids.append(day[2] + day[0] + day[1] + "{:0>5d}".format(teams.loc[teams['institution'] == away[j]]['id'].item()) + "{:0>5d}".format(teams.loc[teams['institution'] == home[j]]['id'].item()) + str(game[j]))
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
