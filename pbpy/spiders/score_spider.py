import scrapy
from scrapy_splash import SplashRequest
import pandas as pd
from datetime import timedelta, date #build in script that runs everyday for yesterday
import re

teamindex = pd.read_csv('https://raw.githubusercontent.com/milesok/NCAA-Baseball-Analytics/master/data/teams.csv')
def get_abb(team):
    if team[0] == ' ':
        team = team[1:]
    is_ranked = re.search(r'(?:#[0-9]{1,2} )(\w*)', team)
    if not is_ranked is None:
        team = is_ranked.group(1)
        seed = is_ranked.group(0)[:3].replace('#', '').replace(' ', '')
    else:
        seed = ''
    if len(teamindex[teamindex['school'] == team]) < 1:
        team = next((s for s in teamindex['school'] if team in s), None)
    if len(teamindex[teamindex['school'] == team]) > 0:
        abb = teamindex[teamindex['school'] == team].iloc[0]['abbreviation']
        return [abb, team, seed]
    else:
        return ['', team, seed]

class Scorespiderspider(scrapy.Spider):
    name = 'score_spider'
    allowed_domains = ["stats.ncaa.org"]

    def start_requests(self):
        urls = []
        d1 = input('input start date in format yyyy-mm-dd: ')
        d2 = input('input end date in format yyyy-mm-dd: ')
        if '06-30' in d2:
            d2 = d2.replace('06-30', '07-01')
        seasonid = input('input season id: ')
        for n in range(int((date(int(d2[0:4]), int(d2[5:7]), int(d2[8:10])+1)-date(int(d1[0:4]), int(d1[5:7]), int(d1[8:10]))).days)):
            d = date(int(d1[0:4]), int(d1[5:7]), int(d1[8:10])) + timedelta(n)
            d = str(d)
            urls.append([d, "https://stats.ncaa.org/season_divisions/" + seasonid + "/scoreboards?game_date=" + d[5:7] + "%2F" + d[8:10] + "%2F" + d[0:4]])
        for url in urls:
            yield SplashRequest(
                url = url[1],
                callback = self.get_scores,
                endpoint='render.html',
                args={'wait': .1},
                meta = {'date': url[0]}
            )

    def get_scores(self, response):
        date = response.meta['date']
        print('Getting scores from ' + date)
        scores = []
        games = response.xpath("//div[@id='contentarea']/table/tbody/tr/td[5]").getall()
        for i in range(0, len(games)):
            box = 'https://stats.ncaa.org' + str(response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3*i) + "]/td[i]/a/@href").get())
            home = response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 2) + "]/td[2]/a/text()").get()
            if not home is None:
                [home_abb, home, home_seed] = get_abb(home)
            else:
                [home_abb, home, home_seed] = ['','','']
            home_score = response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 2) + "]/td[@class='totalcol']/text()").get().replace(' ', '')
            if '\n' in home_score:
                home_score = home_score .replace('\n', '')
            away = response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 1) + "]/td[3]/a/text()").get()
            if not away is None:
                [away_abb, away, away_seed] = get_abb(away)
            else:
                [away_abb, away, away_seed] = ['','','']
            away_score = response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 1) + "]/td[@class='totalcol']/text()").get().replace(' ', '')
            if '\n' in away_score:
                away_score = away_score .replace('\n', '')
            location = response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 1) + "]/td[6]/text()[2]").get()
            if not location is None:
                if '\n' in location:
                    location = location.replace('\n', '')
            innings = len(response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 1) + "]/td[4]/table/tbody/tr[1]/td/text()").getall())
            scores.append([home, home_abb, home_seed, home_score, away, away_abb, away_seed, away_score, location, innings, date])

        df=pd.DataFrame(scores, columns=['home', 'home_abb', 'home_seed', 'home_score', 'away', 'away_abb', 'away_seed', 'away_score', 'location', 'innings', 'date'])
        df.to_csv('scores' + date[0:4] + '.csv', mode = 'a', index = False, header = False)
