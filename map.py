"""
Simple interactive map with toggleable layers using Folium.

Features:
- Base map
- Toggle layers
- Layer control UI

Run:
    python3 map.py

Output:
    japlanning_map.html
"""

# ============================================================
# IMPORT LIBRARIES
# ============================================================

import os
import glob
import folium
import pandas as pd
from folium.plugins import MarkerCluster
from folium.plugins import Draw
import gpxpy
import random
from pathlib import Path
import csv
import math
from shapely.geometry import MultiPoint
from shapely import convex_hull

# ============================================================
# GLOBAL SETTINGS
# ============================================================

popup_max_width = 375
output_file = "japlanning_map.html"

# ============================================================
# FUNCTIONS
# ============================================================

def random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)

def load_icons(csv_file):
    lookup = {}

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["category"], row["subcategory"])

            # store remaining columns
            lookup[key] = {
                "iconset": row["iconset"],
                "icon": row["icon"],
                "color": row["color"],
            }

    return lookup

def get_icon(lookup, field1, field2):

    # if field2 is NaN, match only on field1
    if isinstance(field2, float) and math.isnan(field2):

        for (k1, k2), value in lookup.items():
            if k1 == field1:
                return value

        return None

    # normal lookup
    return lookup.get((field1, field2))

def add_csv_polygon_to_layer(csv_file, layer, color="blue", fill_color="blue", fill_opacity=0.10):
    df = pd.read_csv(csv_file)

    # Skip empty files
    if df.empty:
        return

    # Group coordinates by area_name
    grouped = df.groupby("area_name")

    for area_name, group in grouped:

        # Create coordinate list
        coords = list(zip(group["lat"], group["lon"]))

        # Skip invalid polygons
        if len(coords) < 3:
            continue

        # Add polygon to layer
        folium.Polygon(
            locations=coords,
            popup=area_name,
            color=color,
            fill=True,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            weight=2
        ).add_to(layer)

# ============================================================
# CREATE BASE MAP
# ============================================================

m = folium.Map(
    location=[35.303919,137.817993],
    zoom_start=8,
    max_zoom=19,
    tiles=None
)

# ============================================================
# LOAD MAP LAYERS
# ============================================================

folium.TileLayer(
    tiles="Esri WorldImagery",
    name="Satellite",
    overlay=False,
    control=True
).add_to(m)

folium.TileLayer(
    tiles="CartoDB Positron",
    name="Light Map",
    overlay=False,
    control=True
).add_to(m)

'''
folium.TileLayer(
    tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    attr='Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap',
    name="OpenTopoMap",
    overlay=False,
    control=True
).add_to(m)
'''

# ============================================================
# DAILY LAYER
# ============================================================

'''
points = MultiPoint([(0,0),(1,5),(4,6)])
hull = convex_hull(points)
expanded_smooth_hull = hull.buffer(margin_distance, resolution=16)
'''

# ============================================================
# WARD LAYER
# ============================================================

ward_layer = folium.FeatureGroup(name="Japan wards", show=True)

# Load active wards list
with open('active_wards', 'r') as f:
    active_wards = [line.strip() for line in f.readlines()]

# Load polygons from CSV
CSV_FOLDER = "wards"
csv_files = glob.glob(os.path.join(CSV_FOLDER, "*.csv"))
for csv_file in csv_files:

    df = pd.read_csv(csv_file)

    # Skip empty files
    if df.empty:
        continue

    # Group coordinates by area_name
    grouped = df.groupby("area_name")

    for area_name, group in grouped:

        # Create coordinate list
        coords = list(zip(group["lat"], group["lon"]))

        # Skip invalid polygons
        if len(coords) < 3:
            continue

        if area_name in active_wards:
            # Add polygon to layer
            folium.Polygon(
                locations=coords,
                popup=area_name,
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.05,
                weight=2
            ).add_to(ward_layer)

ward_layer.add_to(m)

# ============================================================
# NATIONAL PARK LAYER
# ============================================================
'''
np_layer = folium.FeatureGroup(name="Japan national parks", show=True)

# Load polygons from CSV
CSV_FOLDER = "parks"
csv_files = glob.glob(os.path.join(CSV_FOLDER, "*.csv"))
for csv_file in csv_files:

    df = pd.read_csv(csv_file)

    # Skip empty files
    if df.empty:
        continue

    # Group coordinates by area_name
    grouped = df.groupby("area_name")

    for area_name, group in grouped:

        # Create coordinate list
        coords = list(zip(group["lat"], group["lon"]))

        # Skip invalid polygons
        if len(coords) < 3:
            continue

        # Add polygon to layer
        folium.Polygon(
            locations=coords,
            popup=area_name,
            color="green",
            fill=True,
            fill_color="green",
            fill_opacity=0.05,
            weight=2
        ).add_to(np_layer)

np_layer.add_to(m)
'''

# ============================================================
# READ MARKER KEY in "marker_icons.csv"
# ============================================================

icons = load_icons("marker_icons.csv")

# ============================================================
# READ ALL PLACES in "japan_places.csv"
# if place is a marker, add a marker
# if place is a polygon, read the polygon_file for the name of the csv in the areas folder
# ============================================================

df = pd.read_csv("japan_places.csv")

# category,subcategory,specific_type,place_name,google_plus_code,lat,lon,metadata,dimension

# Sort by layer, then sublayer
df = df.sort_values(by=["category", "subcategory", "specific_type"])

# Create FeatureGroups and clusters per layer
for layer_name, layer_df in df.groupby("category"):

    # Create layer
    feature_group = folium.FeatureGroup(name=layer_name)

    # Add places
    for _, row in layer_df.iterrows():
        if pd.notnull(row["place_name"]) and str(row["place_name"]).strip() != "" and pd.notnull(row["lat"]) and str(row["lat"]).strip() != "" and pd.notnull(row["lon"]) and str(row["lon"]).strip() != "":
            search_term = "+".join(row["place_name"].strip().split())
            if pd.isna(row["subcategory"]) or str(row["subcategory"]).strip() == "":
                popup_name = row["category"] + ": " + row["specific_type"] + ": " + f"<a href=\"https://www.google.com/search?q={search_term}\">" + "<span style=\"color: darkblue;\">" + row["place_name"] + "</span></a>"
            else:
                popup_name = row["category"] + ": " + row["subcategory"] + ": " + row["specific_type"] + ": " + f"<a href=\"https://www.google.com/search?q={search_term}\">" + "<span style=\"color: darkblue;\">" + row["place_name"] + "</span></a>"

            popup_name = "<span style=\"color: darkgray; font-weight: bold;\">" + popup_name + "</span>"

            if pd.notnull(row["metadata"]) and str(row["metadata"]).strip() != "":
                popup_name = popup_name + ":<br>" + row["metadata"]

            popup = folium.Popup(popup_name, max_width=popup_max_width)

            icon = get_icon(icons, row["category"], row["subcategory"])

            if not icon:
                print ("icon not found", row["category"], row["subcategory"])

            marker = folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=popup,
                icon=folium.Icon(
                    color=icon["color"],
                    icon=icon["icon"],
                    prefix=icon["iconset"]
                )
            )
            feature_group.add_child(marker)
            
            if row["dimension"] == "polygon" and pd.notnull(row["polygon_file"]) and str(row["polygon_file"]).strip() != "":
                add_csv_polygon_to_layer(os.path.join("areas", row["polygon_file"]), feature_group, color="green", fill_color="green", fill_opacity=0.30)

    # Add layer to map
    m.add_child(feature_group)

# ============================================================
# Hiking layer
# - trails from alltrails
# - sorted by difficulty
# ============================================================

hiking_routes_layer = folium.FeatureGroup(name="Hiking routes", show=True)

df = pd.read_csv("hiking_metadata.csv", keep_default_na=False)

# gpx_file,title,difficulty,distance,ele_gain,est_time,type,description

for _, row in df.iterrows():
    popup_name = "<span style=\"color: darkblue;font-weight: bold;\">" + str(row["title"]) + "</span><br>" + \
                 "<span style=\"color: darkgray;font-weight: bold;\">Difficulty:</span> " + str(row["difficulty"]) + "<br>" + \
                 "<span style=\"color: darkgray;font-weight: bold;\">Distance:</span> " + str(row["distance"]) + "<br>" + \
                 "<span style=\"color: darkgray;font-weight: bold;\">Elevation gain:</span> " + str(row["ele_gain"]) + "<br>" + \
                 "<span style=\"color: darkgray;font-weight: bold;\">Estimated time:</span> " + str(row["est_time"]) + "<br>" + \
                 "<span style=\"color: darkgray;font-weight: bold;\">Type:</span> " + str(row["type"]) + "<br>" + \
                 "<span style=\"color: black;\">" + str(row["description"]) + "</span>"

    popup = folium.Popup(popup_name, max_width=popup_max_width)

    file_path = os.path.join("hiking routes", row["gpx_file"])

    if os.path.exists(file_path):
        with open(file_path, "r") as gpx_file:
            gpx = gpxpy.parse(gpx_file)
    else:
        continue

    # Extract track coordinates
    coords = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                coords.append([point.latitude, point.longitude])

    # Create polyline - border of hiking trail
    folium.PolyLine(
        locations=coords,
        color="brown",
        weight=4,
        opacity=0.8
    ).add_to(hiking_routes_layer)

    # Create polyline - inner line of hiking trail
    folium.PolyLine(
        locations=coords,
        color=random_color(),
        weight=2,
        opacity=0.8
    ).add_to(hiking_routes_layer)

    # Create polyline - invisible clickable line to open popup
    folium.PolyLine(
        locations=coords,
        color="white",
        weight=10,
        opacity=0.0,
        popup=popup
    ).add_to(hiking_routes_layer)
    
hiking_routes_layer.add_to(m)

# ============================================================
# Transportation layer
# ============================================================

transportation_layer = folium.FeatureGroup(name="Train lines", show=True)

df = pd.read_csv("train_metadata.csv", keep_default_na=False)

for _, row in df.iterrows():
    popup_name = "<span style=\"color: darkblue;font-weight: bold;\">" + str(row["title"]) + "</span><br>" + \
                 "<span style=\"color: black;\">" + str(row["description"]) + "</span>"

    popup = folium.Popup(popup_name, max_width=popup_max_width)

    file_path = os.path.join("train lines", row["gpx_file"])

    if os.path.exists(file_path):
        with open(file_path, "r") as gpx_file:
            gpx = gpxpy.parse(gpx_file)
    else:
        continue

    for track in gpx.tracks:
        for idx, segment in enumerate(track.segments):
            coords = []
            for point in segment.points:
                coords.append([point.latitude, point.longitude])

            # Create polyline
            folium.PolyLine(
                locations=coords,
                color="grey",
                weight=4,
                opacity=0.8
            ).add_to(transportation_layer)

            # Create polyline
            folium.PolyLine(
                locations=coords,
                color="grey",
                weight=10,
                opacity=0.0,
                popup=popup
            ).add_to(transportation_layer)

transportation_layer.add_to(m)

# ============================================================
# LAYER CONTROL
# ============================================================
folium.LayerControl(position='bottomright', collapsed=True).add_to(m)

# Add custom buttons
select_js = """
<script>
function setAllLayers(checked) {
    document.querySelectorAll('.leaflet-control-layers-selector').forEach(function(el) {
        if (el.checked !== checked) {
            el.click();
        }
    });
}
</script>
"""

buttons_html = """
<div style="
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 9999;
">
    <button onclick="setAllLayers(true)">Select all layers</button>
    <button onclick="setAllLayers(false)">Deselect all layers</button>
</div>
"""

m.get_root().html.add_child(folium.Element(select_js))
m.get_root().html.add_child(folium.Element(buttons_html))

# ============================================================
# ENABLE DRAWING CONTROLS (to draw a polygon for example)
# ============================================================

#Draw(export=True).add_to(m)

# ============================================================
# SAVE MAP
# ============================================================

m.save(output_file)

print(f"Map saved to: {output_file}")