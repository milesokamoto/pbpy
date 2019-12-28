import dict
import names

def parse(text):
    [event, code] = get_event(text)
    primary = get_primary(text, event)
    return [primary, code]

def get_event(text):
    return [[key, dict.codes[key]] for key in dict.codes.keys() if key in text][0]

def get_loc(text):
    return [dict.loc_codes[key] for key in dict.loc_codes.keys() if key in text][0]

def get_primary(text, event):
    return text.split(' ' + event)[0]

def get_run(text):
    return [[key, dict.run_codes[key]] for key in dict.run_codes.keys() if key in text][0]
