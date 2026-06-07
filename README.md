# japlanning
Plan japan

<img width="1262" height="703" alt="preview" src="https://github.com/user-attachments/assets/6a7e7332-75b6-4ba0-91e7-a8eeca1af4c9" />


To build the html file:

For macOS
```python
python3 map.py
```

For Windows
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
pip install -r requirements.txt
```


