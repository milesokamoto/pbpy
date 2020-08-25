import requests
import lxml.html as lh
import pandas as pd

base_url = 'https://stats.ncaa.org'
for year in range(2015, 2017):
    year = 2020
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
    headers = []
    # roster_links.index('/team/545/roster/15204')
    for r in roster_links[19:]:
        log = []
        player_links = []
        roster = requests.get(base_url + r).content
        player_list = lh.fromstring(roster).xpath('//tbody/tr')
        for i in range(len(player_list)):
            team.append(r.split('/')[2])
            jersey.append(player_list[i][0].text)
            if len(player_list[i][1]) > 0:
                players.append(player_list[i][1][0].text)
                ids.append(player_list[i][1][0].attrib['href'].split('seq=')[-1])
                player_links.append(player_list[i][1][0].attrib['href'])
            else:
                players.append(player_list[i][1].text)
                ids.append('')
            pos.append(player_list[i][2].text)
            yr.append(player_list[i][3].text)
        for pl in player_links:
            player_id = pl.split("stats_player_seq=")[1].split('&org_id=')[0]
            hit_gl = requests.get(base_url + pl).content
            hit_tbl = lh.fromstring(hit_gl).xpath("//div[@id='game_breakdown_div']/table/tr/td/table[@class='mytable']/tr")
            pit_gl_url = base_url + lh.fromstring(hit_gl).xpath("//tr[@class='heading']/td[2]/a/@href")[0]
            pit_gl = requests.get(pit_gl_url).content
            pit_tbl = lh.fromstring(pit_gl).xpath("//div[@id='game_breakdown_div']/table/tr/td/table[@class='mytable']/tr")
            fld_gl_url = base_url + lh.fromstring(hit_gl).xpath("//tr[@class='heading']/td[3]/a/@href")[0]
            fld_gl = requests.get(fld_gl_url).content
            fld_tbl = lh.fromstring(fld_gl).xpath("//div[@id='game_breakdown_div']/table/tr/td/table[@class='mytable']/tr")
            
            #hitting
            if len(headers) == 0:
                headers.append("player_id")
                th = hit_tbl[1]
                for h in th:
                    headers.append(h.text)
                headers[3] = "game_id"
            if len(headers) < 25:
                th = pit_tbl[1]
                headers.append(th[3].text)
                for h in th[5:]:
                    headers.append(h.text)
            if len(headers) < 57:
                th = fld_tbl[1]
                for h in th[4:]:
                    headers.append(h.text)
                gl = pd.DataFrame([], columns = headers)
                gl.to_csv('data/tables/gamelogs/gamelogs' + str(year) + '.csv', index=False)

            for i in range(2, len(hit_tbl)):
                hit_tr = hit_tbl[i]
                if hit_tr[3][0].text.strip() == '1':
                    game = [player_id]
                    pit_tr = pit_tbl[i]
                    fld_tr = fld_tbl[i]
                    for td in hit_tr[0:2]:
                        if len(td)>0:
                            game.append(td[0].text.replace('\n','').replace(' ',''))
                        else:
                            game.append(td.text)
                    game.append(hit_tr[2][0].attrib['href'].split('index/')[1].split('?org_id')[0])
                    for tr in [hit_tr, pit_tr, fld_tr]:
                        for td in tr[3:]:
                            if len(td)>0:
                                game.append(td[0].text.replace('\n','').replace(' ',''))
                            else:
                                game.append(td.text)
                    del game[56]
                    del game[24]
                    log.append(game)
        gl = pd.DataFrame(log, columns = headers)
        gl.to_csv('data/tables/gamelogs/gamelogs' + str(year) + '.csv', index=False, mode='a', header=False)
        

    season_id = [link.split('/')[3]]*len(ids)
    player_table = pd.DataFrame({'player_id':ids, 'player':players, 'pos':pos})
    playerseasons = pd.DataFrame({'team_id': team, 'player_id':ids, 'season_id':season_id, 'year':yr, 'jersey':jersey})

    playerseasons.to_csv('data/tables/rosters/rosters' + str(year) + '.csv', index=False)
    player_table.to_csv('data/tables/players/players' + str(year) + '.csv', index=False)
