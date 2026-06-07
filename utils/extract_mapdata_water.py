import os
import geopandas as gpd
import pandas as pd
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def extract_csv(shapefile, target_folder):

    # Output folders
    CSV_OUTPUT_DIR = target_folder

    gdf = gpd.read_file(shapefile)
    gdf = gdf.to_crs(epsg=4326)

    #print("Columns:")
    #print(gdf.columns)
    #print(f"\nLoaded {len(gdf)} city boundaries")

    CITY_NAME_COLUMN = "FULLNAME"

    for idx, row in gdf.iterrows():

        city_name = str(row[CITY_NAME_COLUMN])

        # Clean filename
        safe_name = (
            city_name
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        geometry = row.geometry
        rows = []

        # Handle Polygon
        if geometry.geom_type == "Polygon":
            coords = list(geometry.exterior.coords)
            for lon, lat in coords:
                rows.append({
                    "area_name": city_name,
                    "lat": lat,
                    "lon": lon
                })

        # Handle MultiPolygon
        elif geometry.geom_type == "MultiPolygon":
            for polygon_index, polygon in enumerate(geometry.geoms):
                coords = list(polygon.exterior.coords)
                for lon, lat in coords:
                    rows.append({
                        "area_name": f"{city_name}_{polygon_index}",
                        "lat": lat,
                        "lon": lon
                    })

        csv_df = pd.DataFrame(rows)

        csv_path = os.path.join(
            CSV_OUTPUT_DIR,
            f"{safe_name}.csv"
        )

        csv_df.to_csv(csv_path, index=False)


# Paths
source_dir = Path("water_shape_files")
target_root = Path("water")

# Create target root if it doesn't exist
target_root.mkdir(exist_ok=True)

# Pattern to extract county name
pattern = re.compile(
    r"TIGER/Line Shapefile, Current, County,\s*(.*?),\s*NC"
)

# Find all .shp.iso.xml files
for xml_file in source_dir.rglob("*.shp.iso.xml"):
    try:
        # Read XML as text
        text = xml_file.read_text(errors="ignore")

        # Search for county name
        match = pattern.search(text)

        if match:
            county_name = match.group(1).strip()

            # Optional: clean folder name
            county_name = county_name.replace("/", "-")

            # Create county folder
            county_folder = target_root / county_name
            county_folder.mkdir(exist_ok=True)

            print(f"Created: {county_folder}")

            # Find .shp files in the same folder
            shp_files = list(xml_file.parent.glob("*.shp"))

            if shp_files:
                for shp_file in shp_files:
                    extract_csv(shp_file, county_folder)

        else:
            print(f"No county match found in {xml_file.name}")

    except Exception as e:
        print(f"Error processing {xml_file.name}: {e}")
