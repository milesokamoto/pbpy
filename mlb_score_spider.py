import scrapy
from scrapy_splash import SplashRequest
import pandas as pd
from datetime import timedelta, date #build in script that runs everyday for yesterday
import re

teamindex = pd.read_csv('https://raw.githubusercontent.com/milesok/pbpy/master/teams.csv')

def get_abb(team):
    if team[0] == ' ':
        team = team.split(' ')[1]
    is_ranked = re.search(r'(?:#[0-9]{1,2} )(\w*)', team)
    if not is_ranked is None:
        team = is_ranked.group(1)
    if len(teamindex[teamindex['school'] == team]) < 1:
        team = next((s for s in teamindex['school'] if team in s), None)
    if len(teamindex[teamindex['school'] == team]) > 0:
        abb = teamindex[teamindex['school'] == team].iloc[0]['abbreviation']
        return abb
    else:
        return ''

class Mlbspiderspider(scrapy.Spider):
    name = 'mlb_score_spider'
    allowed_domains = ["http://statsapi.mlb.com"]

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
            urls.append([d, "http://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&date=" + d[5:7] + "/" + d[8:10] + "/" + d[0:4]])
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
        scoreboard = response.xpath("//body/pre").get()
        for i in range(0, len(games)):
            try:
                box = 'https://stats.ncaa.org' + str(response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3*i) + "]/td[i]/a/@href").get())
                home = response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 2) + "]/td[2]/a/text()").get()
                home_abb = get_abb(home)
                home_score = response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 2) + "]/td[@class='totalcol']/text()").get().replace(' ', '').replace('\n', '')
                away = response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 1) + "]/td[3]/a/text()").get()
                away_abb = get_abb(away)
                away_score = response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 1) + "]/td[@class='totalcol']/text()").get().replace(' ', '').replace('\n', '')
                location = response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 1) + "]/td[6]/text()[2]").get().replace('\n', '')
                innings = len(response.xpath("//div[@id='contentarea']/table/tbody/tr[" + str(3 * i + 1) + "]/td[4]/table/tbody/tr[1]/td/text()").getall())
                scores.append([home, home_abb, home_score, away, away_abb, away_score, location, innings, date])
            except:
                continue
        df=pd.DataFrame(scores, columns=['home', 'home_abb', 'home_score', 'away', 'away_abb', 'away_score', 'location', 'innings', 'date'])
        df.to_csv('scores' + date[0:4] + '.csv', mode = 'a', index = False, header = False)
