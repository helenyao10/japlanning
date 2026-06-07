import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union
from pathlib import Path

# folder containing polygon csv files
folder = Path("../parks/nps_dataset")

# Load active parks list
with open('../active_parks', 'r') as f:
    active_parks = [line.strip() for line in f.readlines()]

polygons = []

# loop through all csv files
for csv_file in folder.glob("*.csv"):
    if not any(active_park in str(csv_file) for active_park in active_parks):
        continue

    print (f'appending {csv_file}')

    df = pd.read_csv(csv_file)

    # assumes columns are named lon, lat
    coords = list(zip(df["lon"], df["lat"]))

    # ensure polygon is closed
    if coords[0] != coords[-1]:
        coords.append(coords[0])

    poly = Polygon(coords)
    polygons.append(poly)

# union all polygons
merged = unary_union(polygons)

# convert result back to dataframe
rows = []

# handle Polygon or MultiPolygon
geoms = [merged] if merged.geom_type == "Polygon" else merged.geoms

for poly_idx, poly in enumerate(geoms):
    x, y = poly.exterior.coords.xy

    for lon, lat in zip(x, y):
        rows.append({
            "polygon_id": poly_idx,
            "lon": lon,
            "lat": lat
        })

out_df = pd.DataFrame(rows)

# save result
out_df.to_csv("union_polygons.csv", index=False)

print("saved union_polygons.csv")