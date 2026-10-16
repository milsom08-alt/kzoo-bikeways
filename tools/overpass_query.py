"""Run one Overpass (OpenStreetMap) query file and save the JSON result.

usage: python tools/overpass_query.py QUERY_FILE OUT_JSON
Data © OpenStreetMap contributors, available under the Open Database License (ODbL).
"""
import json, sys, time, urllib.parse, urllib.request

SERVERS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
           "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
query = open(sys.argv[1]).read()
data = urllib.parse.urlencode({"data": query}).encode()
for attempt in range(6):
    url = SERVERS[attempt % len(SERVERS)]
    try:
        req = urllib.request.Request(url, data=data, headers={"User-Agent": "kzoo-bikeways-fetch/1.0"})
        with urllib.request.urlopen(req, timeout=300) as r:
            j = json.loads(r.read().decode("utf-8"))
        json.dump(j, open(sys.argv[2], "w"))
        print(sys.argv[1], "->", sys.argv[2], len(j.get("elements", [])), "elements from", url)
        sys.exit(0)
    except Exception as e:
        print("  attempt", attempt + 1, url, e, file=sys.stderr); time.sleep(30)
sys.exit("overpass failed: " + sys.argv[1])
