#!/usr/bin/env python3
"""Stage 1b of the data pipeline: add the age-by-age income ranks to counties.json.

The "paths diverge" view needs each county's average income rank at ages 24, 26
and 29 for children of low-income (p25) AND high-income (p75) parents. Stage 1
(build_counties.py) now carries these columns, but it also needs the SEDA files,
which sit behind a registration wall. This script lets you refresh just the
Atlas age columns from the one public file, without SEDA:

    county_outcomes.csv  (Table 5, All Outcomes by County, Race, Gender and
                          Parental Income Percentile; 193 MB unzipped)
    https://www2.census.gov/ces/opportunity/county_outcomes.zip

It joins on the 5-digit county code, the same key as stage 1, and refuses to
write anything unless the values already in counties.json (kfr25, kfr24_25,
kfr29_25) match the raw file, so a bad join fails loudly instead of quietly
drawing the wrong lines.

Usage:  python3 scripts/add_age_paths.py [src_dir]     (default ~/Downloads)
        then: python3 scripts/derive_stats.py
"""
import csv, json, os, sys

SRC = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Downloads')
RAW = os.path.join(SRC, 'county_outcomes.csv')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'counties.json')
if not os.path.exists(RAW):
    sys.exit(f'missing: {RAW}\n(see the docstring at the top of this file)')

NEW = {f'kfr_{age}_pooled_pooled_p{p}': f'kfr{age}_{p}' for age in (24, 26, 29) for p in (25, 75)}
CHECK = {'kfr_pooled_pooled_p25': 'kfr25', 'kfr_24_pooled_pooled_p25': 'kfr24_25',
         'kfr_29_pooled_pooled_p25': 'kfr29_25'}


def num(v):
    try:
        x = float(v)
        return None if x != x else round(x, 4)
    except (TypeError, ValueError):
        return None


csv.field_size_limit(1 << 30)
raw = {}
with open(RAW, newline='') as f:
    r = csv.reader(f)
    head = next(r)
    ix = {c: head.index(c) for c in list(NEW) + list(CHECK) + ['state', 'county']}
    for row in r:
        if not row[ix['state']].strip() or not row[ix['county']].strip():
            continue
        k = f"{int(row[ix['state']]):02d}{int(row[ix['county']]):03d}"
        raw[k] = {c: num(row[ix[c]]) for c in list(NEW) + list(CHECK)}

rows = json.load(open(OUT))
missing, bad = 0, 0
for d in rows:
    src = raw.get(d['fips'])
    if src is None:
        missing += 1
        continue
    for long, short in CHECK.items():
        a, b = d.get(short), src[long]
        if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-4):
            bad += 1
    for long, short in NEW.items():
        d[short] = src[long]

print(f'{len(rows)} counties in counties.json, {len(raw)} in the raw file')
print(f'  not found in raw file: {missing}')
print(f'  regression check, existing values that disagree with the raw file: {bad}')
if missing or bad:
    sys.exit('refusing to write: the join does not reproduce the existing columns')
json.dump(rows, open(OUT, 'w'))
have = sum(1 for d in rows if d.get('kfr29_75') is not None)
print(f'wrote {OUT} ({os.path.getsize(OUT)/1024:.0f} KB); {have} counties have age paths')
