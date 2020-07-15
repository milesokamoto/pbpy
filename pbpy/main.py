import os
from datetime import datetime, timedelta

import pandas as pd

import modules.game as game
import modules.scrape as scrape


def main():
    error_log = []
    ncaa_id = input("Input specific game id or press ENTER to scrape a date: ")
    if ncaa_id != '':
        g = game.Game(ncaa_id)
        g.setup_game()
        output = g.execute_game()
        df = pd.DataFrame(output)
        df.to_csv('output/debug/' + str(ncaa_id) + '.csv')
    else:
        day_input = input("Input start date in format 'MM-DD-YYYY': ")
        end_input = input("Input end date in format 'MM-DD-YYYY': ")
        day = datetime.strptime(day_input, '%m-%d-%Y')
        while day < datetime.strptime(end_input, '%m-%d-%Y'):
            date = datetime.strftime(day, '%m-%d-%Y')
            path = "output/" + date
            try:
                os.mkdir(path)
            except OSError:
                print ("Creation of the directory %s failed" % path)
            else:
                print ("Successfully created the directory %s " % path)
            games = scrape.get_scoreboard(date)
            games["ncaa_id"] = ""
            games["error"] = ""
            for i in range(0, len(games)):
                pct = i/len(games)*100
                print(str(round(pct)) + '%' + ' '*(1 if pct>=10 else 2) + '|' + '-'*round(pct/2) + ' '*round(50-pct/2) + '|')
                ncaa_id = scrape.get_id('https://stats.ncaa.org' + games.iloc[i]['link'])
                if not os.path.isfile("output/" + date + '/' + ncaa_id + '.csv'):
                    games.at[i, "ncaa_id"] = ncaa_id
                    print(games.at[i, 'link'])
                    g = game.Game(ncaa_id)
                    g.setup_game()
                    output = g.execute_game()
                    df = pd.DataFrame(output)
                    df.to_csv('output/' + date + '/' + str(ncaa_id) + '.csv')
            day = day + timedelta(days=1)
            # TODO: Check output score against scoreboard


        #     try:
        #         g.parse_plays()
        #     except:
        #         g.error = True
        #     if g.error:
        #         games.at[i, "error"] = 'ERROR'
        #         error_log.append(ncaa_id)
        #         print("ERROR " + str(games.iloc[i]))
        #     else:
        #         data = []
        #         for row in g.output:
        #             data.append(row)
        #         df = pd.DataFrame(data, columns = g.output[0].keys())
        #         df.to_csv('../output/' + date + '/' + games.iloc[i]['id'] + '.csv', index = False)
        # games.to_csv('../output/meta/' + date + '.csv', index = False)
