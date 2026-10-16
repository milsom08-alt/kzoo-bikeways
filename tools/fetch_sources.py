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
        if bbox:
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

summary = []
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
