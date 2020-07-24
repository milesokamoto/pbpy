import os
from datetime import datetime, timedelta

import pandas as pd

import json

import modules.game as game
import modules.scrape as scrape


def main():
    ncaa_id = input("Input specific game id or press ENTER to scrape a date: ")
    if ncaa_id != '':
        g = game.Game(ncaa_id)
        g.setup_game()
        output = g.execute_game()
        df = pd.DataFrame(output)
        df.to_csv('data/output/debug/' + str(ncaa_id) + '.csv')
    else:
        day_input = input("Input start date in format 'MM-DD-YYYY': ")
        end_input = input("Input end date in format 'MM-DD-YYYY': ")
        day = datetime.strptime(day_input, '%m-%d-%Y')
        while day < datetime.strptime(end_input, '%m-%d-%Y'):
            date = datetime.strftime(day, '%m-%d-%Y')
            raw_path = "data/raw/" + date
            try:
                os.mkdir(raw_path)
            except OSError:
                print ("Creation of the directory %s failed" % raw_path)
            else:
                print ("Successfully created the directory %s " % raw_path)
            path = "data/output/" + date
            try:
                os.mkdir(path)
            except OSError:
                print ("Creation of the directory %s failed" % path)
            else:
                print ("Successfully created the directory %s " % path)
            games = scrape.get_scoreboard(date)
            errors = []
            for i in range(0, len(games)):
                pct = i/len(games)*100
                print(str(round(pct)) + '%' + ' '*(1 if round(pct)>=10 else 2) + '|' + '-'*round(pct/2) + ' '*round(50-pct/2) + '|')
                ncaa_id = scrape.get_id('https://stats.ncaa.org' + games.iloc[i]['link'])
                if not os.path.isfile('data/output/' + date + '/' + ncaa_id + '.csv'):
                    games.at[i, 'ncaa_id'] = ncaa_id
                    print(games.at[i, 'link'])
                    g = game.Game(ncaa_id)
                    if not os.path.isfile('data/raw/' + date + '/' + ncaa_id + '.json'):
                        raw = g.setup_game()
                        with open('data/raw/' + date + '/' + ncaa_id + '.json', 'w') as outfile:
                            json.dump(raw, outfile)
                    else:
                        with open('data/raw/' + date + '/' + ncaa_id + '.json', 'r') as infile:
                            d = json.load(infile)
                        g.reparse_game(d)
                    g.create_plays()
                    output = g.execute_game()
                    if g.error:
                        errors.append(1)
                    else:
                        errors.append(0)
                    df = pd.DataFrame(output)
                    df.to_csv('data/output/' + date + '/' + str(ncaa_id) + '.csv', index=False)
            games['error'] = errors
            games.to_csv('data/games/' + date + '.csv', index=False)
            day = day + timedelta(days=1)
            # TODO: Check output score against scoreboard