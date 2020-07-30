import pandas as pd

gm = pd.read_csv("data/output/02-14-2020/4925736.csv")
players = pd.read_csv("data/tables/players/players2020.csv")
joined = gm.merge(players, left_on='bat_id', right_on='player_id', how='left')

joined.groupby('player').agg({'h_fl': 'sum', 'ab_fl': 'sum'})

event_codes = {
    'FL': 2,
    'GDP': 2,
    'FDP': 2,
    'BINT': 2,
    'KL': 3,
    'KS': 3,
    'SO': 3,
    'SB': 4,
    'DI': 5,
    'CS': 6,
    'PO': 8,
    'WP': 9,
    'PB': 10,
    'BK': 11,
    'BB': 14,
    'IBB': 15,
    'HBP': 16,
    'FC': 19,
    '1B': 20,
    '2B': 21,
    '3B': 22,
    'HR': 23,
    'G': 2,
    'F': 2,
    'P': 2,
    'L': 2,
    'C': 17,
    'E': 18,
    'O': 2,
    'K': 3,
    'DF': 13,
}