import scrape
import game
import pandas as pd
import os
def main():
    error_log = []
    date = '02-15-2019'
    path = "../output/" + date
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
        ncaa_id = scrape.get_id('https://stats.ncaa.org' + games.iloc[i]['link'])
        games.at[i, "ncaa_id"] = ncaa_id
        print(games.at[i, 'link'])
        g = game.Game(ncaa_id)
        try:
            g.parse_plays()
        except:
            g.error = True
        if g.error:
            games.at[i, "error"] = 'ERROR'
            error_log.append(ncaa_id)
            print("ERROR " + str(games.iloc[i]))
        else:
            data = []
            for row in g.output:
                data.append(row)
            df = pd.DataFrame(data, columns = g.output[0].keys())
            df.to_csv('../output/' + date + '/' + games.iloc[i]['id'] + '.csv', index = False)
    games.to_csv('../output/meta/' + date + '.csv', index = False)
main()
