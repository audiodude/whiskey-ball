import json

# Should be 60
GAME_DURATION_SECS = 60
# Should be True
USE_MUSIC = True
# Should be 120 * 1000
BASE_POUR_TIME_MS = 120 * 1000
# Should be 10 * 1000
LIGHT_TIME_MS = 10 * 1000

scoremap = json.load(open('scoremap.json'))
rewardmap = json.load(open('rewardmap.json'))
drinks = rewardmap['drinks']
tiers = rewardmap['tiers']
assert len(drinks) == len(tiers), ('Tiers and drinks do not match, check '
                                   'rewardmap.json')
