import os
import sys
import glob
import gpxpy
import numpy as np
import time

GPX_FOLDER = "hiking_routes"
GPX_SAVE_FOLDER = "hiking_segments"
EPSILON = 0.0001
BIG_EPSILON = 0.0010
BIGGEST_EPSILON = 0.0100
CULL_SHORT_SEGMENTS = 10

# neighbor list parameters
NL_lat_min = 35.083956
NL_lat_max = 36.142311
NL_lat_res = 200
NL_lon_min = -83.051147
NL_lon_max = -81.609192
NL_lon_res = 200
NL_cell_maxpts = 5000
neighbor_list = np.zeros((NL_lat_res, NL_lon_res, NL_cell_maxpts, 4))   # neighbor list of segments (x1,y1,x2,y2)
neighbor_list_count = np.zeros((NL_lat_res, NL_lon_res), dtype=int)

def print_progress(iteration, total, prefix='', suffix='', bar_length=50):
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(bar_length * iteration // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    # \r moves the cursor back to the start of the line
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    
    #if iteration == total:
    #    print() # Print a newline when complete

def closest_distance_vectorized(_x, _y, x1, y1, x2, y2):
    """
    p: Point [_x, _y]
    Endpoints of the segment [[x1, y1], [x2, y2]]
    """
    p, a, b = np.array([_x, _y]), np.array([x1, y1]), np.array([x2, y2])
    ab = b - a
    ap = p - a
    
    ab_len_sq = np.sum(ab * ab, axis=-1)
    
    # Avoid division by zero where a == b
    # Default projection to 0.0 if segment length is 0
    t = np.divide(np.sum(ap * ab, axis=-1), ab_len_sq, 
                  out=np.zeros_like(ab_len_sq), where=ab_len_sq != 0)
    t = np.clip(t, 0.0, 1.0)
    
    nearest = a + t[..., np.newaxis] * ab
    return np.linalg.norm(p - nearest, axis=-1)

def closest_distance_NL(_x, _y):
    # check neighbor list for nearest points and check pt-line distance

    # calculate cell_lat and cell_lon
    cell_lat = int((_x - NL_lat_min)/(NL_lat_max - NL_lat_min) * NL_lat_res)
    cell_lon = int((_y - NL_lon_min)/(NL_lon_max - NL_lon_min) * NL_lon_res)

    # check _x and _y against all points at and around this cell
    dist = NL_lat_max - NL_lat_min
    for _lat in range(max(0, cell_lat - 1), min(neighbor_list.shape[0],cell_lat + 2)):
        for _lon in range(max(0, cell_lon - 1), min(neighbor_list.shape[1],cell_lon + 2)):
            for _n in range(neighbor_list_count[_lat, _lon]):
                dist = min(dist, closest_distance_vectorized(_x, _y, neighbor_list[_lat,_lon,_n, 0],
                                                                     neighbor_list[_lat,_lon,_n, 1],
                                                                     neighbor_list[_lat,_lon,_n, 2],
                                                                     neighbor_list[_lat,_lon,_n, 3]))
    return dist

def coord_overlap_NL(_x, _y, cutoff):
    if closest_distance_NL(_x, _y) < cutoff:
        return True

def coord_overlap(_x, _y, global_segments, new_segment_index, cutoff):
    for i in range(len(global_segments)):
        if i == new_segment_index:
            continue

        for j in range(len(global_segments[i])-1):
            x1 = global_segments[i][j][0]
            y1 = global_segments[i][j][1]
            x2 = global_segments[i][j+1][0]
            y2 = global_segments[i][j+1][1]
            if abs(_x - x1) > BIGGEST_EPSILON and abs(_y - y1) > BIGGEST_EPSILON:
                continue
            elif closest_distance_vectorized(_x, _y, x1, y1, x2, y2) < cutoff:
                return True
    return False

def write_gpx(coords, filename):
    # Create GPX object
    gpx = gpxpy.gpx.GPX()

    # Create a track
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create a segment in the track
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Add points
    for lat, lon in coords:
        point = gpxpy.gpx.GPXTrackPoint(lat, lon)
        gpx_segment.points.append(point)

    # Write to file
    with open(filename, "w") as f:
        f.write(gpx.to_xml())

def add_to_neighborlist(_x1, _y1, _x2, _y2):
    # add segment to neighbor list
    
    # calculate cell_lat and cell_lon
    #print (_x1, _y1)
    cell_lat = int(((_x1+_x2)/2 - NL_lat_min)/(NL_lat_max - NL_lat_min) * NL_lat_res)
    cell_lon = int(((_y1+_y2)/2 - NL_lon_min)/(NL_lon_max - NL_lon_min) * NL_lon_res)

    _n = neighbor_list_count[cell_lat, cell_lon]
    neighbor_list[cell_lat, cell_lon, _n, 0] = _x1
    neighbor_list[cell_lat, cell_lon, _n, 1] = _y1
    neighbor_list[cell_lat, cell_lon, _n, 2] = _x2
    neighbor_list[cell_lat, cell_lon, _n, 3] = _y2
    neighbor_list_count[cell_lat, cell_lon] += 1

    return neighbor_list_count[cell_lat, cell_lon]

def main():

    # Start the timer
    start_time = time.perf_counter()

    global_segments = []
    new_segment_index = 0
    neighbor_list_pressure = 0

    # print out neighbor list stats
    print (f'neighbor list lat cell size {(NL_lat_max - NL_lat_min)/NL_lat_res}')
    print (f'neighbor list lon cell size {(NL_lon_max - NL_lon_min)/NL_lon_res}')

    gpx_files = glob.glob(os.path.join(GPX_FOLDER, "*.gpx"))
    for gpx_file in gpx_files:
        print (f"reading gpx file {gpx_file}")

        # Read GPX file
        with open(gpx_file, "r") as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        for track in gpx.tracks:
            for segment in track.segments:
                coords = []

                for point in segment.points:
                    coords.append([point.latitude, point.longitude])
                
                print (f'{len(coords)} coordinates found in segment')

                # compare segment we just read with the global list of coordinates and create new segments as necessary

                # add new segments to the global_segments list
                writing_new_segment = False
                extends_beyond_existing_segments = False
                for i, (_x, _y) in enumerate(coords):
                    print_progress(i, len(coords)-1, '', f'neighbor list pressure {neighbor_list_pressure}')
                    if not coord_overlap_NL(_x, _y, EPSILON):
                        # this is a new coordinate, so probably also the start of a new segment or the continuation of a new segment
                        if not writing_new_segment:
                            # start of a new segment
                            writing_new_segment = True
                            extends_beyond_existing_segments = False   # we want to check if the current segment we are building exists beyond the global segments
                            global_segments.append([[_x, _y]])
                            new_segment_index = len(global_segments)-1
                            print_progress(i, len(coords)-1, '', f'neighbor list pressure {neighbor_list_pressure}')
                        else:
                            # continue adding to new segment
                            global_segments[new_segment_index].append([_x, _y])
                            if not coord_overlap_NL(_x, _y, BIG_EPSILON):
                                extends_beyond_existing_segments = True
                    else:
                        # this is not a new coordinate, so we need to close out the segment if we were writing one
                        if writing_new_segment:
                            # check if the overlapped point is overlapped with the current segment being read from the file, if so, don't end the segment
                            writing_new_segment = False
                            if len(global_segments[new_segment_index]) <= CULL_SHORT_SEGMENTS:
                                del global_segments[-1]
                                new_segment_index = len(global_segments)-1
                                print_progress(i, len(coords)-1, '', f'neighbor list pressure {neighbor_list_pressure}')
                            elif extends_beyond_existing_segments == False:
                                # we want to remove this segment because it did not extend beyond the global set of segments
                                del global_segments[-1]
                                new_segment_index = len(global_segments)-1
                                print_progress(i, len(coords)-1, '', f'neighbor list pressure {neighbor_list_pressure}')
                            else:
                                # ADD ALL POINTS IN GOOD SEGMENT TO NEIGHBOR LIST HERE
                                for _n in range(len(global_segments[new_segment_index]) - 1):
                                    _x1 = global_segments[new_segment_index][_n][0]
                                    _y1 = global_segments[new_segment_index][_n][1]
                                    _x2 = global_segments[new_segment_index][_n+1][0]
                                    _y2 = global_segments[new_segment_index][_n+1][1]
                                    _neighbor_list_pressure = add_to_neighborlist(_x1, _y1, _x2, _y2)
                                    neighbor_list_pressure = max(_neighbor_list_pressure, neighbor_list_pressure)
                                print_progress(i, len(coords)-1, '', f'neighbor list pressure {neighbor_list_pressure}')
                        else:
                            # we weren't writing a new segment and this is not a new coordinate, so do nothing
                            continue

                if writing_new_segment == True:
                    # ADD ALL POINTS IN GOOD SEGMENT TO NEIGHBOR LIST HERE
                    for _n in range(len(global_segments[new_segment_index]) - 1):
                        _x1 = global_segments[new_segment_index][_n][0]
                        _y1 = global_segments[new_segment_index][_n][1]
                        _x2 = global_segments[new_segment_index][_n+1][0]
                        _y2 = global_segments[new_segment_index][_n+1][1]
                        _neighbor_list_pressure = add_to_neighborlist(_x1, _y1, _x2, _y2)
                        neighbor_list_pressure = max(_neighbor_list_pressure, neighbor_list_pressure)

                print_progress(i, len(coords)-1, '', f'neighbor list pressure {neighbor_list_pressure}')
                print()

    global_segments = [seg for seg in global_segments if len(seg) > CULL_SHORT_SEGMENTS]

    for i, global_segment in enumerate(global_segments):
        write_gpx(global_segment, os.path.join(GPX_SAVE_FOLDER, "segment" + str(i) + ".gpx"))
    
    # End the timer
    end_time = time.perf_counter()

    # Calculate and print elapsed time
    elapsed_time = end_time - start_time
    print(f"The script took {elapsed_time:.4f} seconds to run.")

if __name__ == "__main__":
    main()
