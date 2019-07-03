
### Prereqs
This code requires docker running splash: run this command from powershell to start the server: **docker run -p 8050:8050 scrapinghub/splash**  
To run the spider, navigate to the project directory and run **scrapy crawl ncaaspider2**

```python
import scrapy
from scrapy_splash import SplashRequest
import pandas as pd
from datetime import timedelta, date #build in script that runs everyday for yesterday
import re

teamindex = pd.read_csv('https://github.com/milesok/pbpy/blob/master/teams.csv')
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
        home_subs = []
        away_subs = []
        home_lineup = pd.DataFrame()
        away_lineup = pd.DataFrame()
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
Add non-starters who played in the game to subs list
```python
else:
    testname = testname.replace('\n', '')
    testname = testname.replace('     ', '')
    i = i+1
    name = testname
    if j == 2:
        awaysubs.append(name)
    else:
        homesubs.append(name)
```
End the loop and set the lineup to the corresponding team
```python
else:
            end = True
    if j == 2:
        away_lineup = pd.DataFrame(lineup, columns = ['order', 'name', 'position'])
    else:
        home_lineup = pd.DataFrame(lineup, columns = ['order', 'name', 'position'])
```
Navigate to the play by play page
```python
yield SplashRequest(
    url = response.urljoin(response.xpath("//ul[@id='root']/li[3]/a/@href").get()),
    callback = self.parsegame,
    endpoint = 'render.html',
    args = {'wait':.1},
    meta={"away_lineup": away_lineup, "home_lineup": home_lineup, "away_subs": away_subs, "home_subs": home_subs}
    )
```

### parse_game
retrieve lineups and subs
```python
def parsegame(self, response):
    #collects lineups from pbp step
    away_lineup = response.meta["away_lineup"]
    home_lineup = response.meta["home_lineup"]
    home_subs = response.meta["home_subs"]
    away_subs = response.meta["away_subs"]
    play_info = [] 
    away_score = 0
    home_score = 0

    store_hm_order = 1
    store_aw_order = 1

    runners_dest = ['','','','']
```
Get information about the game **still need to figure out how to differentiate double headers**
```python
innings = response.xpath("//tr[@class='heading']/td[1]/a/text()").getall()[-1] #last listed inning
last = innings[0:len(innings)-9] #numeric value for last listed inning
away = response.xpath("//table[@class='mytable'][1]/tbody/tr[2]/td[1]/a/text()").get() #away team
home = response.xpath("//table[@class='mytable'][1]/tbody/tr[3]/td[1]/a/text()").get() #home team
date = response.xpath("//div[@id='contentarea']/table[3]/tbody/tr[1]/td[2]/text()").get()[9:19]
date = date.replace('/', '')
home_abb = teamindex.loc[teamindex['school'] == home]['abbreviation']
away_abb = teamindex.loc[teamindex['school'] == away]['abbreviation']
gameid = date + '-' + away_abb + '-' + home_abb
```
Loop through each inning in the game
```python
n=0 #event number
for inn in range(1, int(last)+1): #loop through each inning
    inn_outs = 0
    inning = inn
    leadoff_fl = True
    outs = 0
    end = False
    inn_half = 0
    line = 1 #line 2 is first play
    runners = ['','','','']
    runners_dest = ['','','','']
```
Loop through the plays for each inning, checking for valid play descriptions
```python
while not end:
    hit_fl = False
    ab_fl = False
    batter_event_fl = False
    event_fl = False
    event_abb = ''
    event_cd = ''
    line += 1
    event_outs = 0
    if inn_half == 0:
        test = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][1]/text()").get()
        if not test is None:
            play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][1]/text()").get()
            order = store_aw_order
            lineup = away_lineup
        else:
            play = "No Play"
            end = True
            break

    else:
        test = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][3]/text()").get()
        if not test is None:
            play = response.xpath("//table[@class='mytable']["+str(inn+1)+"]/tbody/tr["+str(line)+"]/td[@class='smtext'][3]/text()").get()
            order = store_hm_order
            lineup = hmlineup
        else:
            play = "No Play"
            end = True    
    if end:
        break
```

```python
outs = inn_outs%3
play = play.replace('3a', ':')
play = play.replace(';', ':')
```
Break the play into the hitter part and runner part and find the initial player name
```python
event_txt = play.split(":")[0]
runners_txt = play.split(":")[1:]
player = re.search(r'([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*(?= | [a-z])', event_txt)
if not player is None:
    player = player.group() #this used more to filter out -use lineups to id batters
```
Check if the play is a substitution
```python
subtest = re.search(r'([A-Z]{1}[A-Za-z]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)* ((pinch (ran|hit))|(to [0-9a-z]{1,2})) for ([A-Z]{1}[A-Za-z]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*', event_txt)
if not subtest is None:
    sub_txt = subtest.group()
```
Make substitution to lineups *This could probably be its own method for conciseness*  
```python
if 'pinch' in sub_txt:
    if inn_half == 0:
        lu = awlineup
        subs = awaysubs
    else:
        lu = hmlineup
        subs = homesubs
    if 'hit' in sub_txt:
        subin = re.search(r"([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*(?= | [a-z])(?= pinch hit for)", sub_txt).group()
        subtype = 'off'
        pos = 'PH'

    elif 'ran' in sub_txt:
        subin = re.search(r"([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*(?= | [a-z])(?= pinch ran for)", sub_txt).group()
        subtype = 'off'
        pos = 'PR'
else:
    subin = re.search(r"([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*(?= | [a-z])(?= to [0-9a-z]{1,2})", sub_txt).group()
    pos = (re.search(r'(?<= to )[0-9a-z]{1,2}', sub_txt).group()).upper()
    subtype = 'def'
    if inn_half == 1:
        lu = awlineup
        subs = awaysubs
    else:
        lu = hmlineup
        subs = homesubs
subin = subin.replace('.', '')
if ',' in subin and not ', ' in subin:
    subin = subin.replace(',', ', ')
if ' ' in subin and not ',' in subin:
    subin = subin.split(' ')[1] + ', ' + subin.split(' ')[0]
subfull = next((s for s in subs if subin.lower() in s.lower()), None)
if subfull is None:
    subfull = next((s for s in lu['name'] if subin[0:4].lower() in s.lower()), None)
    problemnames.append(subin)
if 'for' in sub_txt:
    subout = re.search(r"(?<= for )([A-Z]{1}[A-Za-z. ]*[-\'A-Za-z]*[, [A-Za-z.]*]* *)*.", sub_txt).group()
    subout = subout.replace('.', '')
    if ',' in subout and not ', ' in subout:
        subout = subout.replace(',', ', ')
    outfull = next((s for s in lu['name'] if subout.lower() in s.lower()), None)
    if outfull is None:
        outfull = next((s for s in lu['name'] if subout[0:4].lower() in s.lower()), None)
        problemnames.append(subout)
    lu = lu.replace(outfull,subfull)
    print(lu)
lu.replace(lu[lu['name']==subfull].iloc[0]['position'], pos)
if (inn_half == 0 and subtype == 'off') or (inn_half == 1 and subtype == 'def'):
    awlineup = lu
else:
    hmlineup = lu
if subtype == 'PR':
    runners[runners.index(outfull)] = subfull

else:
batter = lineup['name'].iloc[order-1]

#BAT_ID
runners[0] = batter
batter_pos = lineup['position'].iloc[order-1]
```
If it's not a sub, parse the play: *could these all be separate methods?*
```python
else:
batter = lineup['name'].iloc[order-1]
runners[0] = batter
batter_pos = lineup['position'].iloc[order-1] #find in lineup

pitches = re.search(r'\(.+?\)', play)
    if pitches is not None:
        pitches = pitches.group()
    else:
        pitches = ''

strikes = re.search(r'(?<=-)[0-2]', pitches)
if strikes is not None:
    strikes = strikes.group()

balls = re.search(r'[0-3](?=-)', pitches)
if balls is not None:
    balls = balls.group()

seq = re.search(r'[A-Z]*(?=\))', pitches)
if seq is not None:
    seq = seq.group()
```
variables for defensive lineup *(again could be a function?)*
```python
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
```
access runners from list *Should add an element to specify responsible pitcher too*
```python
    run_1st = runners[1]
    run_2nd = runners[2]
    run_3rd = runners[3]
```
Find text for what happened on the play
```python
    event = re.search(r'([sdth][a-z]{3}[rl]ed ((to [a-z]* *[a-z]*)|(up [a-z]* [a-z]*)|(down [a-z]* [a-z]* [a-z]* [a-z]*)|(through [a-z]* [a-z]* [a-z]*)))|([a-z]*ed out( to [0-9a-z]*)*)|(popped up( to [0-9a-z]{1,2}))|(struck out [a-z]*)|(reached[ on]*.*((error by [0-9a-z]{1,2})|fielder\'s choice))|walked|(hit by pitch)|((\w* into \w* play ([0-9a-z]{1,2})*)( to [0-9a-z]{1,2})*)|stole|(out on batter\'s interference)', play)
    if not event is None:
        event = event.group()
    else:
        event = ''
    if 'error' in event:
        err_type = re.search(r'(?<=a )[a-z]*(?= error)', event)
        if not err_type is None:
            err_type = err_type.group()
        else:
            err_type = 'fielding'
        err_by = (re.search(r'(?<=error by) [0-9a-z]{1,2}', event).group()).upper()

    short_event = re.search(r'([sdth][a-z]{3}[rl]ed)|([a-z]*ed out)|(popped up)|(struck out [a-z]*)|error|(fielder\'s choice)|walked|(hit by pitch)|(\w* into \w* play)|(batter\'s interference)', event)
    if short_event is not None:
        short_event = short_event.group()
    else: short_event = ''
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

    batter_adv = re.search(r'(advanced to [a-z]*)|((scored) on (the throw)|(advanced on an error by [a-z0-9]{1,2}))|(out at [a-z]* [0-9a-z]{1,2} to [0-9a-z]{1,2})', event_txt)
    if not batter_adv is None:
        batter_adv = batter_adv.group()
        runners_dest[0] = base_codes[re.search(r'((?<=advanced to )\w*)|(scored)|(out)', batter_adv).group()]
    else:
        batter_adv = ''
    for r in runners_txt:
        runner = re.search(r"^[A-Za-z \'\-,\.]*?(?= (advanced|scored|out))", r)
        if not runner is None:
            runner = runner.group()
        else:
            runner = ''
        if not runner == '':
            runner_outcome = re.search(r"(advanced to \w*|scored|out at \w*)(?!.*(advanced|scored|out))", r).group()
        runner = runner.replace('.', '')
        if ',' in runner and not ', ' in runner:
            runner = runner.replace(',', ', ')
        runnerfull = next((s for s in runners if runner.lower() in s.lower()), None)
        if not runnerfull is None:
            runnerfull = next((s for s in runners if runner[0:4].lower() in s.lower()), None)
            problemnames.append(runner)
        else:
            runnerfull = ''
        if 'advanced' in runner_outcome:
            runners_dest[runners.index(runnerfull)] = base_codes[re.search(r'(?<=advanced to )\w*', runner_outcome).group()]
        elif 'scored' in runner_outcome:
            runners_dest[runners.index(runnerfull)] = 4
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
    elif event_cd ==  24:
        runners_dest[0] = 1
    else:
        runners_dest[0] = 0
        
    for base in range(0,4):
        br = runners[3-base]
        if  br != '':
            if runners_dest[3-base] == '':
                runners_dest[3-base] = 3-base
            dest = runners_dest[3-base]
            if dest > 0:
                runners[dest] = br
            if dest != 3-base:
                runners[3-base] = ''
            if dest == 4:
                if inn_half = 0:
                    away_score += 1
                else:
                    home_score += 1
            if dest == 0:
                inn_outs += 1

    if event_cd in {2,3,14,15,16,17,18,19,20,21,22,23}:
         batter_event_fl = True
    if event_cd in range(1,25):
        event_fl = True
    if event_cd in {2,3,18,19,20,21,22,23}:
        ab_fl = True
    if event_cd in {20,21,22,23}:
        hit_fl = True

    if event_cd == 2:
        out_location = re.search(r'(?<=out to )[0-9a-z]{1,2}', event)
        if not out_location is None:
            out_location = out_location.group()

    event = event.replace(', RBI', '1 RBI')
    rbi = re.search(r'[1-4]*(?= RBI)', event)
    if rbi is not None:
        rbi = rbi.group()

    if inn_outs == 3:
        inn_half = 1
        runners = ['','','','']
        leadoff_fl = True
    elif inn_outs == 6:
        end = True
    else:
        leadoff_fl = False

    # errors = re.findall(r'\w* error by [a-z]{1,2}', play)
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

    if player == '':
        batter_event_fl = False
    if(batter_event_fl):
        order = order+1
        if order == 10:
            order = 1
        if inn_half == 0:
            store_aw_order = order
        else:
            store_hm_order = order

    playout = [date, away, home, inning, outs, pitcher, player, batter, event, event_txt, event_cd, runners_txt, strikes, balls, seq]
    if event_fl:
        playinfo.append(playout)
    print('outs' + str(inn_outs))
```
send to dataframe and save to csv
```python
df=pd.DataFrame(playinfo, columns=['date', 'away', 'home', 'inning', 'outs', 'pitcher', 'player', 'batter', 'event', 'event_txt', 'event_cd', 'runners_txt', 'strikes', 'balls', 'seq'])
df.to_csv('\\pbp\\' + date +'.csv', mode='a', index=False, header=False)
err=pd.DataFrame(problemnames, columns = ['names'])
err.to_csv('\\errors\\err.csv', mode='a', index=False, header=False)
```

