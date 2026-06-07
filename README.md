# japlanning
Here we Plan Japan
Mapping out a fall journey 
With help from Python

Japan Travel Planner is an interactive map-based app designed to make planning a trip to Japan simple and intuitive **for briankoo**. Explore detailed map layers including municipal wards, train and subway lines, and curated points of interest such as parks, restaurants, historical landmarks, shopping districts, entertainment venues, and hiking trails. Click any location marker to view rich details, including descriptions, cultural context, visitor information, travel tips, and tabelog ratings. By combining transportation networks with geographic and cultural insights, the app helps **briankoo** discover destinations, understand how places connect, and build efficient, personalized itineraries across Japan. #generatedbyanLLM

<img width="1085" height="600" alt="preview" src="https://github.com/briankoo/japlanning/blob/main/assets/preview.png" />

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


