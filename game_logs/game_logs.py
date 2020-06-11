import requests
import lxml.html as lh
import pandas as pd

url = "https://stats.ncaa.org/team/473/stats/15204"
base = "https://stats.ncaa.org/"
pitching = "&year_stat_category_id=14761"
fielding = "&year_stat_category_id=14762"

payload = {}
headers= {}

response = requests.request("GET", url)

doc = lh.fromstring(response.content)
links = doc.xpath("//table[@id='stat_grid']/tbody/tr/td/a/@href")
names = doc.xpath("//table[@id='stat_grid']/tbody/tr/td/a/text()")
pos = doc.xpath("//table[@id='stat_grid']/tbody/tr/td[4]/text()")
link = '/player/index?game_sport_year_ctl_id=15204&org_id=29&stats_player_seq=2308336'
for i in range(0, len(links)):
    if pos != "P":
        player_url = base + links[i]
        name = names[i]
        player_response = requests.request("GET", player_url)
        log = lh.fromstring(player_response.content)
        stats = log.xpath("//div[@id='game_breakdown_div']/table/tr/td/table")
        headers = []
        for td in stats[0][1]:
            headers.append(td.text)
        rows = []
        for tr in stats[0][2:]:
            row = []
            for td in tr:
                if len(td) > 0:
                    row.append(td[0].text.replace('\n', '').replace('  ', ''))
                else:
                    row.append(td.text.replace('\n', '').replace('  ', ''))
            rows.append(row)
        game_log = pd.DataFrame(data = rows, columns = headers)
        game_log.to_csv('logs/' + name.replace(', ', '_') + '.csv', index = False)
