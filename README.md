# West Michigan Bikeways – October 2026

An interactive web map of bikeways in the Kalamazoo region, the Grand Rapids area and Ottawa County, Michigan: shared-use paths, bike lanes, bike routes and sharrows, paved shoulders, plus (Kalamazoo region only) the club's recommended roads and gravel routes. Includes a route planner that prefers paths and quiet roads.

**Kalamazoo region** – the Kalamazoo Bicycle Club's *K'zoo Region Bikeways Map* (December 2024, made with RCKC and KATS), updated October 2026:

- **New and open since Dec 2024:** Portage St bike lanes (Cork St to Stockbridge Ave), Fruit Belt Rail Trail (Oshtemo), East Central Trail (Portage), KL Ave path under US-131.
- **Existing but missing from the Dec 2024 map:** Kal-Haven Trail from Bloomingdale to South Haven, Vicksburg Trail north end to the Portage city limit, E Kilgore Rd bike lanes (Sprinkle–Portage Rd), Gull Rd path east segment.
- **Under construction / 2026:** Austin Lake Trail (Portage), KRVT Galesburg to Augusta, KL Ave trail (Copper Beech to US-131), Kalamazoo Ave reconstruction zone.
- **Planned 2027–2030:** City of Kalamazoo and Portage bikeway projects, and Road Commission of Kalamazoo County shoulder-widening projects.

**Grand Rapids area and Ottawa County** – from public GIS data, with duplicates between the two removed:

- GVMC asphalt pathways inventory (updated Dec 2025) and existing on-street bike facilities (updated Sept 2023).
- Ottawa County non-motorized pathways (updated May 2025).
- Path names matched from OpenStreetMap (© OpenStreetMap contributors, ODbL), Michigan DNR trail data and Ottawa County data; major trails link to their official websites.
- New since that data: Ann St separated bike lanes (2025), Wyoming 28th St pedestrian bridge (2025), Idema Explorers Trail Bayou segment (2025), Ada Thornapple River pedestrian bridge (2026), rebuilt Musketawa Trail (2026).
- Under construction: Grand River Greenway segments in Plainfield, Cannon and Ada townships (Rogue River Dr trail, Northland Dr tunnel and trails, Pettis Ave trail, Knapp St bridge), Grand River Edges Trail segments in Grand Rapids, Oxford Trail extension, Idema Explorers Trail Bass River segment.

**In between and beyond** – Van Buren Trail (South Haven–Hartford), Van Buren Spur, Blue Star and Beeline trails (Saugatuck area), Paul Henry–Thornapple Trail and Hastings Riverwalk (Barry County), Plainwell–Otsego path and other paths from Michigan DNR and OpenStreetMap data; the Fred Meijer White Pine Trail extended to Cadillac. **Battle Creek** – the Linear Park (about 29 mi including its branches), from Calhoun County's trail GIS layer. **Three Rivers** – the Riverwalk Trail and a short bike path, from OpenStreetMap. **Berrien County** – the Red Arrow Trail (New Buffalo to Sawyer; Bridgman–Stevensville under construction) and the Lakeshore Trail (Higman Park Rd to Monte Rd), from Friends of Berrien County Trails project pages and OpenStreetMap, drawn along the highways where the paths aren't mapped yet. **Blue Star Trail** – planned segments in Saugatuck, from Douglas to M-89, and in South Haven. Paths taken from OpenStreetMap are © OpenStreetMap contributors and available under the Open Database License (ODbL).

Every line's popup names its source; added projects list their status, dates and sources. Planned dates can change. Use at your own risk.

## Files

- `index.html` – the map (Leaflet, OpenStreetMap basemap, BRouter routing)
- `data/bikeways.json` – map data used by the page
- `data/West-Michigan-Bikeways-Oct2026.kml` – full map for Google Earth
- `data/Kzoo-Map-Oct2026-Layers.zip`, `data/GR-Ottawa-Map-Oct2026-Layers.zip` – one KML per layer, for importing into Google My Maps
- `tools/fetch_sources.py` and `.github/workflows/fetch-sources.yml` – download fresh copies of the source GIS layers to the `sources` branch (run from the Actions tab)
