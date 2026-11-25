#!/usr/bin/env python3
"""Build static/counties.json from the raw Opportunity Atlas and SEDA files.

The raw sources total ~210 MB and are not in this repo. Download them and put
them in the directory given by SRC (default ~/Downloads):

  Opportunity Atlas (no registration) -- census.gov/programs-surveys/ces/data/
  public-use-data/opportunity-atlas-data-tables.html
    county_outcomes.csv    Table 5: All Outcomes by County, Race, Gender and
                           Parental Income Percentile  (184 MB, 10,827 columns)
    cty_covariates.csv     County neighborhood characteristics

  SEDA 6.0 (needs an email registration + Data Use Agreement) -- edopportunity.org
    seda_county_pool_cs_6.0.csv       county mean test scores, grades 3-8
    seda_cov_county_pool_6.0.csv      county covariates (ACS-derived)

Join key: Atlas stores a 2-digit `state` and 3-digit `county` separately; SEDA
stores a 5-digit `sedacounty`. Zero-pad and concatenate the Atlas pair. SEDA is
a strict subset -- 3,134 of the Atlas's 3,219 counties -- so no fuzzy matching
is needed. Puerto Rico, DC and a handful of tiny counties drop out.

Usage:  python3 scripts/build_counties.py [src_dir]
"""
import csv, json, os, sys, statistics as st

SRC = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Downloads')
OUT = os.path.join(os.path.dirname(__file__), '..', 'static', 'counties.json')

def src(name):
    p = os.path.join(SRC, name)
    if not os.path.exists(p):
        sys.exit(f'missing: {p}\n(see the docstring at the top of this file)')
    return p

def fips(state, county):
    return f'{int(state):02d}{int(county):03d}'

def num(v):
    try:
        x = float(v)
        return None if x != x else x
    except (TypeError, ValueError):
        return None

# --- SEDA test scores. The file is long on subgroup; we keep three.
scores = {}
for d in csv.DictReader(open(src('seda_county_pool_cs_6.0.csv'))):
    if not d['sedacounty'].strip():
        continue
    sg = d['subgroup']
    if sg not in ('all', 'ecd', 'nec'):          # all / economically disadvantaged / not
        continue
    k = f"{int(d['sedacounty']):05d}"
    e = scores.setdefault(k, {'name': d['sedacountyname'], 'st': d['stateabb']})
    e[f'score_{sg}'] = num(d['cs_mn_avg_eb'])
    if sg == 'all':
        e['learn'] = num(d['cs_mn_lrn_eb'])

for d in csv.DictReader(open(src('seda_cov_county_pool_6.0.csv'))):
    if not d['sedacounty'].strip():
        continue
    k = f"{int(d['sedacounty']):05d}"
    if k in scores:
        scores[k]['ses'] = num(d.get('sesavgall', ''))

# --- Atlas county covariates
cov = {}
for d in csv.DictReader(open(src('cty_covariates.csv'))):
    if not d['state'].strip() or not d['county'].strip():
        continue
    cov[fips(d['state'], d['county'])] = {
        'cz': d['czname'],
        'poverty': num(d['poor_share2010']),
        'collshare': num(d['frac_coll_plus2010']),
        'singlepar': num(d['singleparent_share2010']),
        'medinc': num(d['med_hhinc2016']),
        'popdens': num(d['popdensity2010']),
        'jobdens': num(d['job_density_2013']),
    }

# Long Atlas column name -> short key used in the app.
FIELDS = {
    'kfr_pooled_pooled_p25': 'kfr25',
    'kfr_pooled_pooled_p50': 'kfr50',
    'kfr_pooled_pooled_p75': 'kfr75',
    'kfr_top20_pooled_pooled_p25': 'top20_25',
    'kfr_top20_pooled_pooled_p75': 'top20_75',
    'kfr_24_pooled_pooled_p25': 'kfr24_25',
    'kfr_29_pooled_pooled_p25': 'kfr29_25',
    'kfr_24_pooled_pooled_p75': 'kfr24_75',   # ages 24, 26, 29 at both ends feed the
    'kfr_29_pooled_pooled_p75': 'kfr29_75',   # "paths diverge" view (add_age_paths.py
    'kfr_26_pooled_pooled_p25': 'kfr26_25',   # refreshes just these from the public file)
    'kfr_26_pooled_pooled_p75': 'kfr26_75',
    'coll_pooled_pooled_p25': 'coll25',
    'coll_pooled_pooled_p75': 'coll75',
    'jail_pooled_pooled_p25': 'jail25',
    'kid_pooled_pooled_n': 'n',
    'kid_pooled_pooled_blw_p50_n': 'n_low',
}

out = []
for d in csv.DictReader(open(src('county_outcomes.csv'))):
    if not d['state'].strip() or not d['county'].strip():
        continue
    k = fips(d['state'], d['county'])
    s, c = scores.get(k), cov.get(k)
    if not s or not c:
        continue
    row = {'fips': k, 'county': s['name'], 'state': s['st'], 'cz': c['cz']}
    for long, short in FIELDS.items():
        row[short] = num(d[long])
    row.update({x: c[x] for x in
                ('poverty', 'collshare', 'singlepar', 'medinc', 'popdens', 'jobdens')})
    row.update({'score': s.get('score_all'), 'score_ecd': s.get('score_ecd'),
                'score_nec': s.get('score_nec'), 'learn': s.get('learn'),
                'ses': s.get('ses')})
    if row['kfr25'] is not None:
        out.append(row)

rnd = lambda x: round(x, 4) if isinstance(x, float) else x
out = [{k: rnd(v) for k, v in r.items()} for r in out]
json.dump(out, open(OUT, 'w'))

print(f'wrote {len(out)} counties, {os.path.getsize(OUT)/1024:.0f} KB -> {OUT}')
# Regression check: these are published figures, so a mismatch means the join broke.
by = {r['fips']: r for r in out}
for f, label, expect in [('37119', 'Mecklenburg NC (Charlotte)', 0.352),
                         ('49035', 'Salt Lake UT', 0.454)]:
    got = by[f]['kfr25']
    flag = 'ok' if abs(got - expect) < 0.002 else 'MISMATCH'
    print(f'  {label:28s} kfr25={got:.3f} (expected {expect:.3f})  {flag}')
print(f"  median p75-p25 gap: "
      f"{st.median([r['kfr75'] - r['kfr25'] for r in out if r['kfr75'] is not None]):.3f}"
      f"  (expected ~0.168)")
