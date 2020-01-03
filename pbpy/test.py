import lineup
import names
lu = lineup.Lineups(4803380)
{name: '' for name in lu.all_names('h')}
n = names.NameDict(lu)
print(n.h_names)
