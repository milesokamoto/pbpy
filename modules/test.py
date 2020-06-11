import lineup
import names
import sub
import game
import play
import dict
import parse
import scrape
import re

import json
import pandas as pd
g = game.Game(4926353)
g.parse_plays()
p = play.Play(g.game[0][0], g)
g.last_play.__dict__
g.names.__dict__
g.runners[1].__dict__

play.get_event(g.game[0][0], '')

g.parse_debug(13,5)
p = g.parse_step()
play.get_event(g.last_play.text, '')
primary = g.names.match_name(p.off_team, get_primary(text, self.event[0]), 'p')[0]
p.__dict__
g.output
