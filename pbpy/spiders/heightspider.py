import scrapy
import pandas as pd
import re
import datetime

people = pd.read_csv("C:/Users/Miles/Documents/UT Baseball/bevoball/data/baseballdatabank-2019.2/core/People.csv")
heights19 = pd.read_csv("C:/Users/Miles/Documents/UT Baseball/bevoball/data/heights19.csv")
people2008 = people[(people['debut'] > '2008-01-01')]
ids = people2008[["bbrefID"]]
ids = ids.rename(columns = {'bbrefID':'bref_id'})
ids = ids.append(heights19[["bref_id"]]).drop_duplicates()
players = []

class HeightSpider(scrapy.Spider):
    name = 'heightspider'
    allowed_domains = ["baseball-reference.com"]
    def start_requests(self):
        urls = []
        for i in range(0, len(ids)):
            try:
                p = ids.iloc[i]['bref_id']
                urls.append('https://www.baseball-reference.com/players/' + p[0] + '/' + p + '.shtml')
            except:
                pass
        for url in urls:
            yield scrapy.Request(url=url, callback = self.parse)
        df = pd.DataFrame(players, columns = ['id', 'height'])
        df.to_csv('heights.csv', mode='a', index=False, header=True)

    def parse(self, response):
        id = response.url.split("/")[-1].split(".")[0]
        try:
            height = response.xpath("//div[@id='info']/div[@id='meta']/div[2]/p[3]/span[1]/text()").get()
            height = int(height.split('-')[0])*12 + int(height.split('-')[1])
            players.append([id, height])
        except:
            pass
