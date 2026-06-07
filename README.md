# japlanning
Plan japan

To build the html file:

```python
python map.py
```

Outputs japlanning.html

## Requirements

### Folders
- **areas**
- **hiking routes**
- **train lines**
- **wards**

### Packages
See requirements.txt for exact versions
- folium
- pandas
- shapely
- gpxpy
- geopandas
- numpy

## Helper scripts in utils

| script | description |
| -- | -- |
| extract_mapdata_water.py |  |
| extract_mapdata.py |  |
| extract_traindata.py |  |
| fix_train_gpx.py |  |
| routes2segments.py |  |
| union_polygons_parkdata.py |  |

## Setup
Tested on Python >=3.11

Instructions for macOS
```bash
python3 -m venv .venv
```

Activate the environment
```bash
source .venv/bin/activate
```

Update pip
```bash
pip3 install --upgrade pip
```

Install packages
```bash
python3 -m pip install -r requirements.txt
```


