import requests
import lxml.html as lh
import pandas as pd

base_url = 'https://stats.ncaa.org'
for year in range(2000, 2020):
    div = str(1)
    ids_url = 'https://stats.ncaa.org/team/inst_team_list?sport_code=MBA&academic_year=' + str(year) + '&division=' + str(div)
    season_teams = requests.get(ids_url).content
    confs = lh.fromstring(season_teams).xpath("//ul[@id='root']/li[7]/ul[@class='level2']/li/a")
    schools = []
    ids = []
    roster_links = []
    conf_ids = []
    conf_names = []
    school_confs = []

    for c in confs[1:]:
        conf_names.append(c.text)
        conf_id = c.attrib['href'].split('(')[1].split(')')[0]
        conf_ids.append(conf_id)
        # getting all links from table of schools in D1 for specified year
        conf_url = 'https://stats.ncaa.org/team/inst_team_list?sport_code=MBA&academic_year=' + str(year) + '&division=' + str(div) + '&conf_id=' + conf_id
        conf_teams = requests.get(conf_url).content
        teams = lh.fromstring(conf_teams).xpath('//td/a')
        for t in teams:
            schools.append(t.text)
            link = t.attrib['href']
            ids.append(link.split('/')[2])
            roster_links.append(link.replace(link.split('/')[3], 'roster/' + link.split('/')[3]))
            school_confs.append(conf_id)
    
    divs = [div]*len(conf_names)
    season_id = [link.split('/')[3]]*len(ids)
    school_table = pd.DataFrame({'school_id':ids, 'school_name':schools}) 
    teamseasons = pd.DataFrame({'season_id':season_id, 'conf_id':school_confs, 'school_id':ids})
    conf_table = pd.DataFrame({'conf_id':conf_ids, 'conf_name':conf_names, 'div':divs})

    school_table.to_csv('data/tables/schools/schools' + str(year) + '.csv', index=False)
    teamseasons.to_csv('data/tables/teamseasons/teamseasons' + str(year) + '.csv', index=False)
    conf_table.to_csv('data/tables/conferences/conferences' + str(year) + '.csv', index=False)

    jersey = []
    players = []
    ids = []
    pos = []
    yr = []
    team = []
    for r in roster_links:
        roster = requests.get(base_url + r).content
        player_list = lh.fromstring(roster).xpath('//tbody/tr')
        for i in range(len(player_list)):
            r='/team/703/roster/15204'
            team.append(r.split('/')[2])
            jersey.append(player_list[i][0].text)
            if len(player_list[i][1]) > 0:
                players.append(player_list[i][1][0].text)
                ids.append(player_list[i][1][0].attrib['href'].split('seq=')[-1])
            else:
                players.append(player_list[i][1].text)
                ids.append('')
            pos.append(player_list[i][2].text)
            yr.append(player_list[i][3].text)
    season_id = [link.split('/')[3]]*len(ids)
    player_table = pd.DataFrame({'player_id':ids, 'player':players, 'pos':pos})
    playerseasons = pd.DataFrame({'team_id': team, 'player_id':ids, 'season_id':season_id, 'year':yr, 'jersey':jersey})

    playerseasons.to_csv('data/tables/rosters/rosters' + str(year) + '.csv', index=False)
    player_table.to_csv('data/tables/players/players' + str(year) + '.csv', index=False)
