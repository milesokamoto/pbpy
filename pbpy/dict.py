import pandas as pd

teamindex = pd.read_csv('https://raw.githubusercontent.com/milesok/ncaa-baseball/master/data/teams.csv')

codes = {
    'singled': '1B',
    'doubled': '2B',
    'tripled': '3B',
    'homered': 'HR',
    'flied out': 'F',
    'flied into double play': 'F',
    'popped up': 'P',
    'popped out': 'P',
    'infield fly': 'P', #label w/ flag?
    'popped into double play': 'F',
    'lined into double play': 'L',
    'lined into triple play': 'L',
    'lined out': 'L',
    'grounded out': 'G',
    'out at first': 'G', ##ONLY FOR BATTERS - check on this for fielding
    'grounded into double play': 'G',
    'hit into double play': 'G',
    'hit into triple play': 'G',
    'fouled into double play': 'F',
    'fouled out': 'F', #when doing fielders, add f after fielder code
    'struck out looking': 'KL',
    'struck out swinging': 'KS',
    'struck out': 'K',
    'struck out ': 'K',
    'hit by pitch': 'HBP',
    'walked': 'BB',
    'stole': 'SB',
    'picked off': 'PO',
    'caught stealing': 'CS',
    'wild pitch': 'WP',
    'passed ball': 'PB',
    'balk': 'BK',
    'batter\'s interference': 'BINT',
    'catcher\'s interference': 'C',
    'error': 'E',
    'fielder\'s choice': 'FC'
}
event_codes = {
    'G': 2,
    'F': 2,
    'P': 2,
    'L': 2,
    'BINT': 2,
    'KL': 3,
    'KS': 3,
    'K': 3,
    'SB': 4,
    'DI': 5,
    'CS': 6,
    'PO': 8,
    'WP': 9,
    'PB': 10,
    'BK': 11,
    'BB': 14,
    'IBB': 15,
    'HBP':16,
    'C': 17,
    'E': 18,
    'FC': 19,
    '1B': 20,
    '2B': 21,
    '3B': 22,
    'HR': 23
}
fielder_codes = {
    'P' : 1,
    'C' : 2,
    '1B' : 3,
    '2B' : 4,
    '3B' : 5,
    'SS' : 6,
    'LF' : 7,
    'CF' : 8,
    'RF' : 9,
    'DH' : 10,
    'PH' : 11
}
base_codes = {
    'first': 1,
    'second': 2,
    'third': 3,
    'home': 4,
    'scored': 4,
    'out': 0
}
loc_codes = {
    'to pitcher': 1,
    'to catcher': 2,
    'to first base': 3,
    'through the right side': 34,
    'to second base': 4,
    'to third base': 5,
    'through the left side': 56,
    'to shortstop': 6,
    'to left field': 7,
    'down the lf line': 7,
    'to left center': 78,
    'to center field': 8,
    'up the middle': 46,
    'to right center': 89,
    'to right': 9,
    'down the rf line': 9
}
