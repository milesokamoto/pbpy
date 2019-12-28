import dict
import names

def parse(text):

def get_code(text):
    event = (dict.codes[key] for key in dict.codes.keys() if key in text)
    return event

parse('Ellis singled down the lf line.')
text = 'Ellis singled down the lf line.'
for item in parse('Ellis singled down the lf line.'):
    print(item)
