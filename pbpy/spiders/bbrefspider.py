import scrapy
import pandas as pd
import re
import datetime

people = pd.read_csv("C:/Users/Miles/Documents/UT Baseball/bevoball/data/baseballdatabank-2019.2/core/People.csv")
people2000 = people[(people['debut'] > '2000-01-01')]
ids = people2000[["bbrefID"]]
players = []

class BbrefSpider(scrapy.Spider):
    name = 'bbrefspider'
    allowed_domains = ["baseball-reference.com"]
    def start_requests(self):
        urls = []
        for i in range(0, len(ids)):
            try:
                p = ids.iloc[i]['bbrefID']
                urls.append('https://www.baseball-reference.com/players/' + p[0] + '/' + p + '.shtml')
            except:
                pass
        for url in urls:
            yield scrapy.Request(url=url, callback = self.parse)
        df = pd.DataFrame(players, columns = ['id', 'drafted', 'hs', 'col'])
        df.to_csv('schools.csv', mode='a', index=False, header=True)

    def parse(self, response):
        id = response.url.split("/")[-1].split(".")[0]
        end = False
        draft = False
        hs = ''
        col = ''
        j=0
        while not end:
            j += 1
            try:
                info = response.xpath("//div[@id='info']/div[@id='meta']/div[2]/p["+ str(j) + "]").get()
                if "High School" in info:
                    hs = response.xpath("//div[@id='info']/div[@id='meta']/div[2]/p["+ str(j) + "]/a/text()").get()
                elif "School" in info:
                    col = response.xpath("//div[@id='info']/div[@id='meta']/div[2]/p["+ str(j) + "]/a/text()").get()
                elif "Drafted" in info:
                    draft = True
            except:
                end = True
        players.append([id, draft, hs, col])
