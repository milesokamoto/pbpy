import pandas as pd

teamindex = pd.read_csv(
    'https://raw.githubusercontent.com/milesok/ncaa-baseball/master/data/teams.csv')

codes = {
    'singled': '1B',
    'doubled': '2B',
    'tripled': '3B',
    'homered': 'HR',
    'flied out': 'O',
    'flied into double play': 'O',
    'flied into triple play': 'FITP',
    'popped up': 'O',
    'popped out': 'O',
    'popped into double play': 'O',
    'lined into double play': 'O',
    'lined into triple play': 'O',
    'lined out': 'O',
    'grounded out': 'O',
    'out at first': 'O',  # ONLY FOR BATTERS - check on this for fielding
    'grounded into double play': 'O',
    'hit into double play': 'O',
    'hit into triple play': 'O',
    'fouled into double play': 'O',
    'fouled out': 'O',  # when doing fielders, add f after fielder code
    'struck out looking': 'SO',
    'struck out swinging': 'SO',
    'struck out': 'SO',
    'hit by pitch': 'HBP',
    'walked': 'BB',
    'stole': 'SB',
    'picked off': 'PO',
    'caught stealing': 'CS',
    'wild pitch': 'WP',
    'passed ball': 'PB',
    'balk': 'BK',
    'batter\'s interference': 'INT',
    'catcher\'s interference': 'INT',
    'reached on a throwing error': 'E',
    'reached on an error': 'E',
    'reached on a fielder\'s choice': 'FC',
    'indifference' : 'DI'
}
mod_codes = {
    'singled': '1B',
    'doubled': '2B',
    'tripled': '3B',
    'homered': 'HR',
    'flied out': 'F',
    'flied into double play': 'FDP',
    'flied into triple play': 'FTP',
    'popped up': 'P',
    'popped out': 'P',
    'infield fly': 'IF',  # label w/ flag?
    'popped into double play': 'PDP',
    'lined into double play': 'LDP',
    'lined into triple play': 'LTP',
    'lined out': 'L',
    'grounded out': 'G',
    'out at first': 'G',  # ONLY FOR BATTERS - check on this for fielding
    'grounded into double play': 'GDP',
    'hit into double play': 'GDP',
    'hit into triple play': 'GTP',
    'fouled into double play': 'FDP',
    'fouled out': 'FL',  # when doing fielders, add f after fielder code
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
    'a throwing error': 'TH',
    'fielder\'s choice': 'FC'
}
event_codes = {
    'G': 2,
    'F': 2,
    'P': 2,
    'L': 2,
    'GIDP': 2,
    'FIDP' : 2,
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
    'HBP': 16,
    'C': 17,
    'E': 18,
    'FC': 19,
    '1B': 20,
    '2B': 21,
    '3B': 22,
    'HR': 23
}
pos_codes = {
    'p': 1,
    'c': 2,
    '1b': 3,
    '2b': 4,
    '3b': 5,
    'ss': 6,
    'lf': 7,
    'cf': 8,
    'rf': 9,
    'dh': 10,
    'ph': 11,
    'pr': 12
}
base_codes = {
    'first': 1,
    'second': 2,
    'third': 3,
    'home': 4,
    'scored': 4,
    'out': 0
}
run_codes = {
    'reached first': 1,
    'advanced to second': 2,
    'stole second': 2,
    'advanced to third': 3,
    'stole third': 3,
    'scored': 4,
    'stole home': 4,
    'out at first': 5,
    'out at second': 6,
    'out at third': 7,
    'out at home': 8,
    'out on the play': 10
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
sub_codes = {
'pinch hit for' : 'PH',
'pinch ran for' : 'PR',
' to ' : 'DEF'
}
