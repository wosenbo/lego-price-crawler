MAX_THREAD_NUM = 5

SITES = ['bricklink', 'lego']

REGIONS = {
    'United States': 'en-US',
    'Japan': 'ja-JP',
    'Australia': 'en-AU',
    'Germany': 'en-DE',
    'Danmark': 'en-DK',
    'United Kingdom': 'en-GB'
}

REGIONS_LOC = {}
for region in REGIONS:
    REGIONS_LOC[REGIONS[region]] = region


class Status:
    ERROR = -1
    INIT = 0
    PROCESSING = 1
    DONE = 6
