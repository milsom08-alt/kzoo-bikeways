"""Download public bikeway GIS layers as GeoJSON (WGS84) into ./out.

Run by .github/workflows/fetch-sources.yml; results are committed to the
`sources` branch so the map data can be rebuilt from exact copies.
"""
import json, os, sys, time, urllib.parse, urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
os.makedirs(OUT, exist_ok=True)
SW_MI = "-86.70,41.70,-84.90,43.45"   # SW Michigan envelope for statewide layers

SOURCES = [
    # name, service URL, layer ids (None = all), extra where/geometry filter
    ("gvmc_pathways",      "https://services5.arcgis.com/X42k956XlfnIoN3d/arcgis/rest/services/Asphalt_Pathways_WFL1/FeatureServer", [2], None),
    ("gvmc_onstreet",      "https://services5.arcgis.com/X42k956XlfnIoN3d/arcgis/rest/services/On_Street_Existing_Bike_Facility/FeatureServer", None, None),
    ("gvmc_tip_onstreet",  "https://services5.arcgis.com/X42k956XlfnIoN3d/arcgis/rest/services/OnStreetBikeFY26_29TIP/FeatureServer", None, None),
    ("gvmc_tip_offstreet", "https://services5.arcgis.com/X42k956XlfnIoN3d/arcgis/rest/services/OffStSharedUseFY26_29TIP/FeatureServer", None, None),
    ("gvmc_river_trail",   "https://services5.arcgis.com/X42k956XlfnIoN3d/arcgis/rest/services/River_Trail/FeatureServer", None, None),
    ("ottawa_nonmotorized","https://gis.miottawa.org/arcgis/rest/services/HostedServices/NonMotorizedPathways/FeatureServer", None, None),
    ("dnr_railtrails",     "https://gisagoegle.state.mi.us/arcgis/rest/services/DNR/DNRTrailsOPENDATA/MapServer", [16], SW_MI),
    ("dnr_biking",         "https://gisagoegle.state.mi.us/arcgis/rest/services/DNR/DNRTrailsOPENDATA/MapServer", [3], SW_MI),
    ("dnr_whitepine",      "https://gisagoegle.state.mi.us/arcgis/rest/services/DNR/DNRTrailsOPENDATA/MapServer", [16], {"where": "RailGradeName LIKE '%White Pine%'"}),
    ("calhoun_trails",     "https://services7.arcgis.com/3kp3Io7Dw56fpgk8/arcgis/rest/services/Trail/FeatureServer", [9, 1, 0], None),
    ("kats_existing",      "https://services8.arcgis.com/iMB25Rg6ZW5ZL5YH/arcgis/rest/services/Existing_Facilities_October_2026/FeatureServer", None, None),
]

def get(url, params=None, tries=4):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kzoo-bikeways-fetch/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("  retry", i + 1, e, file=sys.stderr)
            time.sleep(3 * (i + 1))
    raise RuntimeError("failed: " + url)

def fetch_layer(base, lid, bbox):
    meta = get(f"{base}/{lid}", {"f": "json"})
    if meta.get("type") not in (None, "Feature Layer") or meta.get("geometryType") not in ("esriGeometryPolyline", "esriGeometryPoint", "esriGeometryMultipoint", None):
        return meta, None
    page = min(int(meta.get("maxRecordCount") or 1000), 1000)
    feats, off = [], 0
    while True:
        p = {"where": "1=1", "outFields": "*", "outSR": 4326, "f": "geojson",
             "resultOffset": off, "resultRecordCount": page, "orderByFields": meta.get("objectIdField") or "OBJECTID"}
        if isinstance(bbox, dict):
            p.update(bbox)
        elif bbox:
            p.update({"geometry": bbox, "geometryType": "esriGeometryEnvelope", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects"})
        gj = get(f"{base}/{lid}/query", p)
        if "error" in gj:
            raise RuntimeError(json.dumps(gj["error"]))
        got = gj.get("features", [])
        feats += got
        if len(got) < page and not gj.get("exceededTransferLimit") and not (gj.get("properties") or {}).get("exceededTransferLimit"):
            break
        if not got:
            break
        off += len(got)
    return meta, {"type": "FeatureCollection", "features": feats}

OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
OSM_BBOX = "42.74,-86.32,43.32,-85.28"   # Grand Rapids area + Ottawa County (south,west,north,east)
OSM_QUERY = f"""[out:json][timeout:300];
way["highway"~"^(cycleway|path|footway|track|bridleway)$"]["name"]({OSM_BBOX});
out tags geom;
relation["route"~"^(bicycle|mtb|hiking|foot|fitness_trail)$"]["name"]({OSM_BBOX});
out body geom;"""

GAP_BBOX = "42.05,-86.40,42.80,-85.15"   # South Haven - Kalamazoo - Hastings - southern Kent
GAP_QUERY = f"""[out:json][timeout:300];
(
  way["highway"="cycleway"]({GAP_BBOX});
  way["highway"~"^(path|footway|track)$"]["bicycle"~"^(designated|yes)$"]({GAP_BBOX});
  way["highway"~"^(path|footway|track|cycleway)$"]["name"]({GAP_BBOX});
);
out tags geom;
relation["route"~"^(bicycle|mtb)$"]({GAP_BBOX});
out body geom;"""

BC_BBOX = "42.20,-85.33,42.42,-85.03"    # Battle Creek (Linear Park and connecting paths)
BC_QUERY = f"""[out:json][timeout:300];
(
  way["highway"="cycleway"]({BC_BBOX});
  way["highway"~"^(path|footway|track)$"]["bicycle"~"^(designated|yes)$"]({BC_BBOX});
  way["highway"~"^(path|footway|track|cycleway)$"]["name"]({BC_BBOX});
);
out tags geom;
relation["route"~"^(bicycle|mtb|hiking|foot)$"]({BC_BBOX});
out body geom;"""

# Small towns: every non-sidewalk path (named or not), to check for local trails
TOWNS_QUERY = """[out:json][timeout:300];
(
  way["highway"~"^(path|footway|cycleway)$"]["footway"!~"^(sidewalk|crossing|traffic_island)$"](41.85,-85.80,42.08,-85.45);
  way["highway"~"^(path|footway|cycleway)$"]["footway"!~"^(sidewalk|crossing|traffic_island)$"](42.42,-85.95,42.58,-85.62);
);
out tags geom;
relation["route"~"^(bicycle|hiking|foot)$"](41.85,-85.80,42.08,-85.45);
out tags;"""

# Roads along the Blue Star Trail corridor (South Haven - Saugatuck), for drawing planned segments
BLUESTAR_ROADS = """[out:json][timeout:300];
way["highway"]["name"~"Blue Star|North St|66th|Holland St|Wiley|Baseline|Old Allegan|Lake St|Center St|Washington|Water St|Butler|Culver|Phillips|Ferry|Main St|M-89|124th|122nd|126th"](42.38,-86.30,42.70,-86.15);
out tags geom;"""

# Berrien County lakeshore (Lakeshore Trail, Red Arrow Trail)
BERRIEN_QUERY = """[out:json][timeout:300];
(
  way["highway"="cycleway"](41.75,-86.82,42.22,-86.30);
  way["highway"~"^(path|footway|track)$"]["bicycle"~"^(designated|yes)$"](41.75,-86.82,42.22,-86.30);
  way["highway"~"^(path|footway|cycleway)$"]["name"](41.75,-86.82,42.22,-86.30);
);
out tags geom;
relation["route"~"^(bicycle|hiking|foot)$"](41.75,-86.82,42.22,-86.30);
out body geom;"""

def fetch_osm_query(query, fname):
    data = urllib.parse.urlencode({"data": query}).encode()
    for i, url in enumerate(OVERPASS * 2):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "kzoo-bikeways-fetch/1.0"})
            with urllib.request.urlopen(req, timeout=400) as r:
                j = json.loads(r.read().decode("utf-8"))
            json.dump(j, open(os.path.join(OUT, fname), "w"))
            return len(j.get("elements", []))
        except Exception as e:
            print("  overpass retry", i + 1, e, file=sys.stderr); time.sleep(20)
    raise RuntimeError("overpass failed")

def fetch_osm():
    """Named paths and trail route relations from OpenStreetMap (© OpenStreetMap contributors, ODbL)."""
    data = urllib.parse.urlencode({"data": OSM_QUERY}).encode()
    for i, url in enumerate(OVERPASS * 2):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "kzoo-bikeways-fetch/1.0"})
            with urllib.request.urlopen(req, timeout=400) as r:
                j = json.loads(r.read().decode("utf-8"))
            json.dump(j, open(os.path.join(OUT, "osm_named_trails.json"), "w"))
            return len(j.get("elements", []))
        except Exception as e:
            print("  overpass retry", i + 1, e, file=sys.stderr); time.sleep(20)
    raise RuntimeError("overpass failed")

summary = []
try:
    n = fetch_osm(); summary.append({"file": "osm_named_trails", "elements": n, "license": "ODbL, (c) OpenStreetMap contributors"})
    print("osm_named_trails:", n, "elements")
except Exception as e:
    summary.append({"file": "osm_named_trails", "error": str(e)}); print("ERROR osm", e, file=sys.stderr)
try:
    n = fetch_osm_query(GAP_QUERY, "osm_gap_paths.json"); summary.append({"file": "osm_gap_paths", "elements": n, "license": "ODbL, (c) OpenStreetMap contributors"})
    print("osm_gap_paths:", n, "elements")
except Exception as e:
    summary.append({"file": "osm_gap_paths", "error": str(e)}); print("ERROR osm gap", e, file=sys.stderr)
try:
    n = fetch_osm_query(BC_QUERY, "osm_battle_creek.json"); summary.append({"file": "osm_battle_creek", "elements": n, "license": "ODbL, (c) OpenStreetMap contributors"})
    print("osm_battle_creek:", n, "elements")
except Exception as e:
    summary.append({"file": "osm_battle_creek", "error": str(e)}); print("ERROR osm bc", e, file=sys.stderr)
try:
    n = fetch_osm_query(TOWNS_QUERY, "osm_towns.json"); summary.append({"file": "osm_towns", "elements": n, "license": "ODbL, (c) OpenStreetMap contributors"})
    print("osm_towns:", n, "elements")
except Exception as e:
    summary.append({"file": "osm_towns", "error": str(e)}); print("ERROR osm towns", e, file=sys.stderr)
try:
    n = fetch_osm_query(BLUESTAR_ROADS, "osm_bluestar_roads.json"); summary.append({"file": "osm_bluestar_roads", "elements": n, "license": "ODbL, (c) OpenStreetMap contributors"})
    print("osm_bluestar_roads:", n, "elements")
except Exception as e:
    summary.append({"file": "osm_bluestar_roads", "error": str(e)}); print("ERROR osm bluestar", e, file=sys.stderr)
try:
    n = fetch_osm_query(BERRIEN_QUERY, "osm_berrien.json"); summary.append({"file": "osm_berrien", "elements": n, "license": "ODbL, (c) OpenStreetMap contributors"})
    print("osm_berrien:", n, "elements")
except Exception as e:
    summary.append({"file": "osm_berrien", "error": str(e)}); print("ERROR osm berrien", e, file=sys.stderr)
for name, base, layers, bbox in SOURCES:
    try:
        svc = get(base, {"f": "json"})
        ids = layers if layers is not None else [l["id"] for l in svc.get("layers", [])]
        for lid in ids:
            meta, fc = fetch_layer(base, lid, bbox)
            fn = f"{name}__{lid}"
            json.dump(meta, open(os.path.join(OUT, fn + ".meta.json"), "w"), indent=1)
            if fc is None:
                continue
            json.dump(fc, open(os.path.join(OUT, fn + ".geojson"), "w"))
            ei = meta.get("editingInfo") or {}
            summary.append({"file": fn, "layer": meta.get("name"), "features": len(fc["features"]),
                            "lastEditDate": ei.get("lastEditDate") or ei.get("dataLastEditDate"), "url": f"{base}/{lid}"})
            print(f"{fn}: {meta.get('name')} -> {len(fc['features'])} features")
    except Exception as e:
        summary.append({"file": name, "error": str(e)})
        print("ERROR", name, e, file=sys.stderr)
json.dump({"fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "layers": summary},
          open(os.path.join(OUT, "SUMMARY.json"), "w"), indent=1)
