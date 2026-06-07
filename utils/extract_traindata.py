import geopandas as gpd
import gpxpy
import gpxpy.gpx
from pathlib import Path

gpkg_file = "hotosm_jpn_railways_lines_gpkg.gpkg"
output_dir = Path("train lines")

output_dir.mkdir(exist_ok=True)

# Read file
gdf = gpd.read_file(gpkg_file)

# GPX requires WGS84
gdf = gdf.to_crs(epsg=4326)

# Dictionary of GPX objects
routes = {}

for idx, row in gdf.iterrows():

    geom = row.geometry

    # Skip unsupported geometry
    if geom is None:
        continue

    # Get route name
    name = str(row["name:en"]).strip()

    if not name:
        name = f"route_{idx}"

    # Create GPX if first time seeing this name
    if name not in routes:

        gpx = gpxpy.gpx.GPX()

        track = gpxpy.gpx.GPXTrack(name=name)

        gpx.tracks.append(track)

        routes[name] = gpx

    else:
        gpx = routes[name]
        track = gpx.tracks[0]

    # Normalize geometry types
    if geom.geom_type == "LineString":
        lines = [geom]

    elif geom.geom_type == "MultiLineString":
        lines = list(geom.geoms)

    else:
        continue

    # Add each line as a separate segment
    for line in lines:

        segment = gpxpy.gpx.GPXTrackSegment()

        for lon, lat, *rest in line.coords:

            elevation = rest[0] if rest else None

            point = gpxpy.gpx.GPXTrackPoint(
                latitude=lat,
                longitude=lon,
                elevation=elevation
            )

            segment.points.append(point)

        track.segments.append(segment)

# Write all GPX files
for name, gpx in routes.items():

    safe_name = (
        name
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    output_path = output_dir / f"{safe_name}.gpx"

    with open(output_path, "w") as f:
        f.write(gpx.to_xml())

    print(f"Saved: {output_path}")