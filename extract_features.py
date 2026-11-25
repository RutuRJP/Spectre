import sys

current = {}

def process_run(d):
    try:
        ipc = d['instructions'] / d['cycles']
        bmr = d['branch_miss'] / d['branches'] * 100
        cmr = d['cache_miss'] / d['cache_refs'] * 100
        print(ipc, bmr, cmr, d['cycles'])
    except KeyError:
        # skip incomplete runs
        pass

for line in sys.stdin:

    parts = line.strip().split(',')

    if len(parts) < 3:
        continue

    value = parts[0].replace(',', '')
    event = parts[2]

    if 'cycles' in event:
        current['cycles'] = float(value)

    elif 'instructions' in event:
        current['instructions'] = float(value)

    elif 'branch-misses' in event:
        current['branch_miss'] = float(value)

    elif 'branches' in event:
        current['branches'] = float(value)

    elif 'cache-misses' in event:
        current['cache_miss'] = float(value)

    elif 'cache-references' in event:
        current['cache_refs'] = float(value)

        # assume run ends here
        process_run(current)
        current = {}
