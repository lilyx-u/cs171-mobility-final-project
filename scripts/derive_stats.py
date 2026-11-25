#!/usr/bin/env python3
"""Stage 2 of the data pipeline: derive the summary numbers the story page quotes.

Reads static/counties.json (built by build_counties.py from the raw Atlas + SEDA
files) and writes static/derived.json with everything the narrative needs that
is cheaper to compute once than in the browser:

  national      - means, standard deviations and p10/p90 spread of outcomes at
                  each parental percentile, over reliable counties (n >= 1000)
  correlations  - Pearson r of each county characteristic with kfr25 and kfr75
  density_bins  - mean kfr25 by order-of-magnitude of population density
  ages          - mean rank at 24, 26, 29 and in the mid-thirties, for children
                  of low-income and high-income parents
  regions       - state abbreviation -> Census region (for filtering the fan)
  twins         - pairs of counties with near-identical kfr25 but very different
                  p75-p25 gaps (feeds the "same outcome, opposite structure" draft)
  examples      - a few named counties used in the prose

No third-party packages: only the standard library, so it runs anywhere.

Usage:  python3 scripts/derive_stats.py
"""
import json, math, os, statistics as st
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'static', 'counties.json')
OUT = os.path.join(HERE, '..', 'static', 'derived.json')
MIN_N = 1000

REGIONS = {
    'Northeast': 'CT ME MA NH RI VT NJ NY PA',
    'Midwest': 'IL IN MI OH WI IA KS MN MO NE ND SD',
    'South': 'DE FL GA MD NC SC VA DC WV AL KY MS TN AR LA OK TX',
    'West': 'AZ CO ID MT NV NM UT WY AK CA HI OR WA',
}
STATE_REGION = {s: r for r, ss in REGIONS.items() for s in ss.split()}

rows = json.load(open(SRC))
rel = [d for d in rows if d['n'] is not None and d['n'] >= MIN_N
       and d['kfr25'] is not None and d['kfr75'] is not None]


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]


def corr(a, b):
    ps = [(d[a], d[b]) for d in rel if d[a] is not None and d[b] is not None]
    ma, mb = st.mean(p[0] for p in ps), st.mean(p[1] for p in ps)
    num = sum((x - ma) * (y - mb) for x, y in ps)
    den = math.sqrt(sum((x - ma) ** 2 for x, _ in ps) * sum((y - mb) ** 2 for _, y in ps))
    return round(num / den, 3)


national = {}
for k in ('kfr25', 'kfr50', 'kfr75'):
    xs = [d[k] for d in rel if d[k] is not None]
    national[k] = {
        'mean': round(st.mean(xs), 4), 'median': round(st.median(xs), 4),
        'sd': round(st.pstdev(xs), 4),
        'p10': round(pct(xs, 0.10), 4), 'p90': round(pct(xs, 0.90), 4),
        'min': round(min(xs), 4), 'max': round(max(xs), 4),
    }
    national[k]['spread'] = round(national[k]['p90'] - national[k]['p10'], 4)
gaps = [d['kfr75'] - d['kfr25'] for d in rel]
national['gap'] = {'mean': round(st.mean(gaps), 4), 'median': round(st.median(gaps), 4),
                   'p10': round(pct(gaps, 0.10), 4), 'p90': round(pct(gaps, 0.90), 4)}

CHARS = [('singlepar', 'Single-parent share'), ('poverty', 'Poverty rate'),
         ('score', 'Test scores (all students)'), ('score_ecd', 'Test scores (low-income students)'),
         ('score_nec', 'Test scores (not low-income)'), ('medinc', 'Median household income'),
         ('collshare', 'Share of adults with a BA'), ('popdens', 'Population density')]
correlations = [{'key': k, 'label': lab, 'r25': corr(k, 'kfr25'), 'r75': corr(k, 'kfr75')}
                for k, lab in CHARS]

bins = {}
for d in rel:
    if d['popdens'] and d['popdens'] > 0:
        b = min(4, int(math.log10(max(d['popdens'], 1))))
        bins.setdefault(b, []).append(d)
density_bins = [{'bin': b,
                 'label': f"{10**b:,}-{10**(b+1):,} per sq mi" if b < 4 else '10,000+ per sq mi',
                 'n': len(v), 'kfr25': round(st.mean(x['kfr25'] for x in v), 4),
                 'kfr75': round(st.mean(x['kfr75'] for x in v), 4)}
                for b, v in sorted(bins.items())]

# Mean rank at each age, both parent groups, over counties that report all of them.
AGE_KEYS = [f'kfr{a}_{p}' for a in (24, 26, 29) for p in (25, 75)]
aged = [d for d in rel if all(d.get(k) is not None for k in AGE_KEYS)]
ages = {k: round(st.mean(d[k] for d in aged), 4) for k in AGE_KEYS}
ages['adult_25'] = round(st.mean(d['kfr25'] for d in aged), 4)
ages['adult_75'] = round(st.mean(d['kfr75'] for d in aged), 4)
ages['n'] = len(aged)

# Twins: big counties (n >= 20k) with kfr25 within 0.5 points but gaps >= 8 points apart.
big = [d for d in rel if d['n'] >= 20000]
twins = []
for a, b in combinations(big, 2):
    if abs(a['kfr25'] - b['kfr25']) < 0.005:
        ga, gb = a['kfr75'] - a['kfr25'], b['kfr75'] - b['kfr25']
        if abs(ga - gb) >= 0.08:
            lo, hi = (a, b) if ga < gb else (b, a)
            twins.append({'flat': {'fips': lo['fips'], 'name': f"{lo['county']}, {lo['state']}",
                                   'kfr25': lo['kfr25'], 'kfr75': lo['kfr75']},
                          'steep': {'fips': hi['fips'], 'name': f"{hi['county']}, {hi['state']}",
                                    'kfr25': hi['kfr25'], 'kfr75': hi['kfr75']},
                          'gap_diff': round(abs(ga - gb), 4)})
twins.sort(key=lambda t: -t['gap_diff'])
twins = twins[:12]

by = {d['fips']: d for d in rows}


def ex(f):
    d = by[f]
    return {'fips': f, 'name': f"{d['county']}, {d['state']}", 'kfr25': d['kfr25'],
            'kfr75': d['kfr75'], 'gap': round(d['kfr75'] - d['kfr25'], 4), 'n': d['n']}


examples = {k: ex(f) for k, f in [('charlotte', '37119'), ('saltlake', '49035'),
                                   ('middlesex', '25017'), ('cook', '17031'),
                                   ('dubuque', '19061')]}

best = sorted(big, key=lambda d: -d['kfr25'])[:5]
worst = sorted(big, key=lambda d: d['kfr25'])[:5]
extremes = {'best_p25': [ex(d['fips']) for d in best], 'worst_p25': [ex(d['fips']) for d in worst]}

out = {'counties_total': len(rows), 'counties_reliable': len(rel), 'min_n': MIN_N,
       'national': national, 'correlations': correlations, 'density_bins': density_bins,
       'ages': ages, 'regions': STATE_REGION, 'twins': twins, 'examples': examples,
       'extremes': extremes}
json.dump(out, open(OUT, 'w'), indent=1)
print(f"wrote {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")
print(f"  reliable counties: {len(rel)} of {len(rows)}")
for k in ('kfr25', 'kfr50', 'kfr75'):
    print(f"  {k}: mean {national[k]['mean']:.3f}  sd {national[k]['sd']:.3f}  "
          f"p10-p90 spread {national[k]['spread']:.3f}")
print(f"  strongest predictor of kfr25: {max(correlations, key=lambda c: abs(c['r25']))['label']}")
if twins:
    print(f"  twins found: {len(twins)}  e.g. {twins[0]['flat']['name']} vs {twins[0]['steep']['name']}")
