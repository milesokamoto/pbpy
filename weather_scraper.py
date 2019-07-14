import sys
import datetime
import json
import pandas as pd
import urllib.request

teamindex = pd.read_csv('https://raw.githubusercontent.com/milesok/.csv')

apikey = "3dcd9552b6151c3201db99e9bf4620ef"
lat = 30.279243
lat =  teamindex[teamindex['school'] == home].iloc[0]['abbreviation']
long = -97.726663

data = []

if apikey == "YOUR_APIKEY_HERE":
    print("Make sure to update the script with your Darksky apikey - find it at https://darksky.net/dev/account.")
    print("More info in the Appendix")
    sys.exit()

api_url_base = "https://api.darksky.net/forecast/%s/" % apikey
max_days_back = 918
start_date = datetime.datetime.today() - datetime.timedelta(days=(max_days_back + 1))
for days_back in range(max_days_back):
    date = start_date + datetime.timedelta(days=days_back)
    date_string = date.strftime('%Y-%m-%d')
    url = api_url_base + "%s,%s,%sT12:00:00" % (lat, long, date_string)
    res = urllib.request.urlopen(url).read()
    try:
        print("Grabbing data for %s" % date_string)
        weather_data = json.loads(res)
        weather_data = weather_data
        weather_data.update({ "date": date_string })
        data.append(weather_data)
    except:
        print("Trouble loading data for %s" % date_string)

data_file = open('my_weather_data.json', 'w')
data_file.seek(0)
data_file.truncate()
data_file.write(json.dumps(data))
