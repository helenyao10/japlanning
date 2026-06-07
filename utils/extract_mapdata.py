import os
import geopandas as gpd
import pandas as pd
from pathlib import Path
import re
import xml.etree.ElementTree as ET

target_root = Path("../parks")
OUTPUT_FOLDER = "nps_dataset"

def extract_csv(shapefile, target_folder):

    # Output folders
    CSV_OUTPUT_DIR = target_folder

    gdf = gpd.read_file(shapefile)
    gdf = gdf.to_crs(epsg=4326)

    print("Columns:")
    print(gdf.columns)
    print("examples")
    print(gdf.iloc[0])
    print(f"\nLoaded {len(gdf)} boundaries")

    NAME_COLUMN = "NAME"
    unique = []
    counts = []

    for idx, row in gdf.iterrows():

        name = str(row[NAME_COLUMN])
        
        if name not in unique:
            unique.append(name)
            counts.append(0)
            counter = 0
        else:
            idx = unique.index(name)
            counts[idx] += 1
            counter = counts[idx]

        # Clean filename
        safe_name = (
            name
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        safe_name = safe_name + str(counter)

        geometry = row.geometry
        rows = []

        # Handle Polygon
        if geometry.geom_type == "Polygon":
            coords = list(geometry.exterior.coords)
            for lon, lat in coords:
                rows.append({
                    "area_name": safe_name,
                    "lat": lat,
                    "lon": lon
                })

        # Handle MultiPolygon
        elif geometry.geom_type == "MultiPolygon":
            for polygon_index, polygon in enumerate(geometry.geoms):
                coords = list(polygon.exterior.coords)
                for lon, lat in coords:
                    rows.append({
                        "area_name": f"{safe_name}_{polygon_index}",
                        "lat": lat,
                        "lon": lon
                    })

        csv_df = pd.DataFrame(rows)

        csv_path = os.path.join(
            CSV_OUTPUT_DIR,
            f"{safe_name}.csv"
        )

        csv_df.to_csv(csv_path, index=False)


# Create target root if it doesn't exist
target_root.mkdir(exist_ok=True)

# Create target subrolder if it doesn't exist
target_child = target_root / OUTPUT_FOLDER
target_child.mkdir(exist_ok=True)

# Find all .shp.iso.xml files
extract_csv("../raw data/japan_national_parks/nps.shp", target_child)
