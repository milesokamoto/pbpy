
### Prereqs
This code requires docker running splash: run this command from powershell to start the server: **docker run -p 8050:8050 scrapinghub/splash**  
To run the spider, navigate to the project directory and run **scrapy crawl ncaaspider2**

```python
import scrapy
from scrapy_splash import SplashRequest
import pandas as pd
from datetime import timedelta, date #build in script that runs everyday for yesterday
import re
```

### Class definition
```python
class ncaaspider2(scrapy.Spider):
    name = "ncaaspider2"
    allowed_domains = ["stats.ncaa.org"]
```

### start_requests
Loops through dates in the given range and constructs urls to the ncaa scoreboard page for those days. Then makes splash requests for each url.
```python
def start_requests(self):
        urls = []
        for n in range(int((date(2019,2,15) - date(2019,2,14)).days)):
            d = date(2019,2,15) + timedelta(n)
            d = str(d)
            urls.append("https://stats.ncaa.org/season_divisions/16800/scoreboards?game_date="
                + d[5:7] + "%2F" + d[8:10] + "%2F" + d[0:4]))

        for url in urls:
            yield SplashRequest(
                url = url,
                callback = self.parse,
                endpoint='render.html',
                args={'wait': .1},
            )
```

### parse
Method finds all box score links on scoreboard page and loops through sending each one to parse method

```python
def parse(self, response):
        links = response.xpath("//div[@id='contentarea']/table/tbody/tr/td[1]/a[@class='skipMask']/@href").getall()
        for link in links:
            abs_url = response.urljoin(link)
            yield SplashRequest(
                url = abs_url,
                callback = self.lineups,
                endpoint='render.html',
                args={'wait': .1}
                )
```

### lineup
Create empty containers for lineup info
```python
def lineups(self, response):
        homelineup = []
        awaylineup = []
        homesubs = []
        awaysubs = []
        hlineup = pd.DataFrame()
        alineup = pd.DataFrame()
```
Loop for away and home lineups on box score page
```python
        #2 and 3 represent elements for away and home lineups
        for j in {2,3}:
            end = False
            lineup = []
            i = 1
            order = 1
```

```python
        while not end:
            testname = response.xpath("//table[@class='mytable']["+str(j)+"]/tbody/tr[@class='smtext'][" + str(i) + "]/td[1]/a/text()").get()
            if testname is None: #would happen if it's not a link
                testname = response.xpath("//table[@class='mytable']["+str(j)+"]/tbody/tr[@class='smtext'][" + str(i) + "]/td[1]/text()").get()
            if not testname is None and not testname == 'Totals' :
                testname = testname.replace('\xa0', ' ') #replaces spaces in name field
```
Add starters to lineup
```python
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
                    order = order + 1
                i = i+1
```

```python
```

```python
```

```python
```

```python
```
