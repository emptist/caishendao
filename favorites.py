from settings_spy500stks import spy500stks
from settings_pairs import pairs,pair_list
from settings_gists import gists
from settings_favors import favors
from settings_now_down import now_down
from settings_top_sp import top_sp
from settings_ns100 import ns100
from settings_bio import bios
from settings_indices import indices

class MyFavorites:    
    pick_ups = {
        'BITX',
        'GDXD',
        'GDXU',
        'GOSS',
        'LABU',
        'LABD',
        'SGRT',
        'SHLD',
        'SPXU',
        'SQQQ',
        'TQQQ',
        'UPRO',
    }
    
    
    chosen_underlines = [
        #"GOSS",
        "SPY",
        "QQQ",
        #"IBIT",
    ]
    
    indices = indices
    now_down = now_down
    bios = bios.union(gists).union(pick_ups)
    spy500stks = spy500stks
    ns100 = ns100
    top_sp = top_sp
    gists = gists.union(now_down).union(pick_ups)
    favors = favors.union(gists)

    pairs = pairs
    pair_list = pair_list
    # use pair_list to generate a dictionary, with each string in one line of pair_list as a keys and values to each other
    pairs_dict = {}
    for i in range(0, len(pair_list), 2):
        pairs_dict[pair_list[i]] = pair_list[i + 1]
        pairs_dict[pair_list[i + 1]] = pair_list[i]
    # print the dictionary
    # print(pairs_dict[pair_list[0]])
    # print(pairs_dict[pair_list[1]])
    pairs_4_trade = pair_list
    pairs_4_trade.reverse()

    bull_sp = top_sp.union(pairs)
    bull_pool = favors.union(pairs)
    # bull_pool = ['CRWV','DOMO'] # for testing


    @staticmethod
    def wanted_opt_underlines(symbol):
        if symbol in MyFavorites.chosen_underlines:
            return True
        elif symbol[:1] in ["XL", "xl"]:
            return True
        else:
            return False
