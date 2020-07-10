import modules.game as game
import modules.names as names
id = 4926019
g = game.Game(id)
g.play_list = game.get_pbp(id)
for lu in g.lineups:
    names.match_all(lu, g.play_list)
g.check_subs()
print(g.check_order())