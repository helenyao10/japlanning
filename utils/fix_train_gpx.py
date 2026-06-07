import sys
import gpxpy
import math
from collections import defaultdict

# define

MAX_GAP = 3000
INPUT_FILE = "train lines/Tokaido Shinkansen.gpx"
OUTPUT_FILE = "tokaido_shinkansen_fixed.gpx"

# tokyo station
start_lat = 35.681312500000004
start_lon = 139.7670625

# starting direction
start_direction = (-1,0)

# shin osaka station
end_lat = 34.7335
end_lon = 135.5007

# functions

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def point_tuple(p):
    return (p.latitude, p.longitude)

def find_next_segment(current_end, direction=(0,0)):
    # find next best segment. direction is optional, but if provided, make sure next best segment is facing the same direction
    best_index = None
    best_distance = float("inf")
    reverse_segment = False

    # check forward segments first
    for i, seg in enumerate(segments):
        if seg["used"]:
            continue

        d = haversine(
            current_end[0], current_end[1],
            seg["start"][0], seg["start"][1]
        )

        if d < best_distance:
            if direction[0] == 0 and direction[1] == 0:
                best_distance = d
                best_index = i
                reverse_segment = False
            elif (seg["direction"][0] - direction[0])**2 + (seg["direction"][1] - direction[1])**2 < 1:
                best_distance = d
                best_index = i
                reverse_segment = False

    if best_distance < MAX_GAP:
        return best_index, best_distance, reverse_segment

    # check reversed segments only if you haven't found a good forward segment
    for i, seg in enumerate(segments):
        if seg["used"]:
            continue

        d = haversine(
            current_end[0], current_end[1],
            seg["end"][0], seg["end"][1]
        )

        if d < best_distance:            
            if direction[0] == 0 and direction[1] == 0:
                best_distance = d
                best_index = i
                reverse_segment = True
            elif (seg["direction"][0] + direction[0])**2 + (seg["direction"][1] + direction[1])**2 < 1:
                best_distance = d
                best_index = i
                reverse_segment = True

    return best_index, best_distance, reverse_segment

# ---------------------------------------------------
# LOAD SEGMENTS
# ---------------------------------------------------

with open(INPUT_FILE, "r") as f:
    gpx = gpxpy.parse(f)

segments = []

for track in gpx.tracks:
    for seg in track.segments:
        pts = seg.points

        if len(pts) < 2:
            continue

        seg_mag = math.sqrt((pts[-1].longitude - pts[0].longitude)**2 + (pts[-1].latitude - pts[0].latitude)**2)

        segments.append({
            "points": pts,
            "start": point_tuple(pts[0]),
            "end": point_tuple(pts[-1]),
            "used": False,
            "direction": ((pts[-1].longitude - pts[0].longitude)/seg_mag, (pts[-1].latitude - pts[0].latitude)/seg_mag)
        })

print(f"Loaded {len(segments)} segments")

#print (haversine(35.683096, 139.768753, 35.682852, 139.768624))

#sys.exit()

# ---------------------------------------------------
# BUILD CONTINUOUS ROUTE
# ---------------------------------------------------

route_points = [gpxpy.gpx.GPXTrackPoint(start_lat, start_lon)]

# find the first segment
idx, dist, revseg = find_next_segment([start_lat, start_lon], start_direction)
segments[idx]["used"] = True
if revseg:
    current_direction = (-segments[idx]["direction"][0], -segments[idx]["direction"][1])
    route_points.extend(reversed(segments[idx]["points"]))
else:
    current_direction = segments[idx]["direction"]
    route_points.extend(segments[idx]["points"])

while True:
    current_end = point_tuple(route_points[-1])
    idx, dist, revseg = find_next_segment(current_end, current_direction)

    if idx is None:
        break

    if dist > MAX_GAP:
        print(f"Stopping. Next segment too far: {dist:.1f} m")
        break

    print (f'adding segment {idx}, reversed {revseg}')

    seg = segments[idx]
    seg["used"] = True
    pts = seg["points"]
    current_direction = seg["direction"]

    if revseg:
        pts = list(reversed(pts))
        current_direction = (-current_direction[0],-current_direction[1])

    next_start = point_tuple(pts[0])

    gap = haversine(
        current_end[0], current_end[1],
        next_start[0], next_start[1]
    )

    # Fill small gap with straight line
    if gap > 0:
        route_points.append(
            gpxpy.gpx.GPXTrackPoint(
                next_start[0],
                next_start[1]
            )
        )

    # avoid duplicate point
    route_points.extend(pts[1:])

    print(f"Added segment {idx}, gap={gap:.1f} m")


# ADD LAST POINT
route_points.append(
    gpxpy.gpx.GPXTrackPoint(
        end_lat,
        end_lon
    )
)

# ---------------------------------------------------
# WRITE OUTPUT
# ---------------------------------------------------

out_gpx = gpxpy.gpx.GPX()

track = gpxpy.gpx.GPXTrack()
out_gpx.tracks.append(track)

segment = gpxpy.gpx.GPXTrackSegment()
track.segments.append(segment)

segment.points = route_points

with open(OUTPUT_FILE, "w") as f:
    f.write(out_gpx.to_xml())

print(f"Wrote {len(route_points)} points")