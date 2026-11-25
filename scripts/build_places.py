"""Pipeline stage 3: cities and towns -> counties, for the search box.

Joins a public city list (city, state, county name) to static/counties.json on
county name within the state, and writes static/places.json as
[[city, state, fips], ...]. A town that sits in two counties appears twice.

Source: https://github.com/kelvins/US-Cities-Database (csv/us_cities.csv,
~29,900 rows, MIT licence). Usage:

    python scripts/build_places.py path/to/us_cities.csv static/counties.json static/places.json
"""
import csv, json, re, sys, unicodedata
from collections import defaultdict
cities_csv, counties_json, out = sys.argv[1:4]
SUFFIX = re.compile(r"\s+(county|parish|borough|census area|municipality|city and borough|city|municipio)$", re.I)
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.strip().lower()
    s = re.sub(r"^(saint|st\.?|sainte|ste\.?)\s+", "st ", s)
    s = re.sub(r"[’']", "", s)
    s = SUFFIX.sub("", s)
    s = SUFFIX.sub("", s)  # "City and Borough" then "Borough"
    return re.sub(r"[^a-z0-9]+", "", s).strip()  # drop spaces: "De Kalb" == "DeKalb"
counties = json.load(open(counties_json, encoding="utf-8"))
idx = defaultdict(list)
for c in counties:
    idx[(c["state"], norm(c["county"]))].append(c)
    # Virginia independent cities: "Richmond city" -> also index as "richmond city"
    if c["county"].endswith(" city"):
        idx[(c["state"], norm(c["county"][:-5]) + "city")].append(c)
places, unmatched, seen = [], defaultdict(int), set()
with open(cities_csv, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        st, city, cty = r["STATE_CODE"], r["CITY"].strip(), r["COUNTY"]
        hits = idx.get((st, norm(cty)))
        if not hits and cty.lower().endswith(" city"):
            hits = idx.get((st, norm(cty)))
        if not hits:
            unmatched[(st, cty)] += 1; continue
        c = hits[0]
        # skip places whose name is already the county's own name: the county search finds them
        key = (city.lower(), st, c["fips"])
        if key in seen: continue
        seen.add(key)
        places.append([city, st, c["fips"]])
places.sort(key=lambda p: (p[0].lower(), p[1]))
json.dump(places, open(out, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
print("places", len(places), "unmatched county keys", len(unmatched), "rows", sum(unmatched.values()))
for k, v in sorted(unmatched.items(), key=lambda kv: -kv[1])[:25]: print(" ", k, v)
