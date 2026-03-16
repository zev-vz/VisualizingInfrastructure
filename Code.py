"""
@author: zevvanzanten
"""
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point
from pathlib import Path
from scipy.spatial import Voronoi

#Data directory path
DATA_DIR = Path('data')

# Global styling (editorial polish)
plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.titleweight": "bold"
})

#My global airport heatmap

def create_airport_heatmap():
    """
    Visualizing airport density with some color-coding by size
    """
    airports = pd.read_csv(DATA_DIR / 'airports.csv')
    world = gpd.read_file(DATA_DIR / 'ne_110m_admin_0_countries.shp')

    airports = airports[airports['type'].isin(['large_airport', 'medium_airport', 'small_airport'])]

    geometry = [Point(xy) for xy in zip(airports['longitude_deg'], airports['latitude_deg'])]
    airports_gdf = gpd.GeoDataFrame(airports, geometry=geometry, crs='EPSG:4326')

    # Project to Robinson for better global aesthetics
    world = world.to_crs("ESRI:54030")
    airports_gdf = airports_gdf.to_crs("ESRI:54030")

    fig, ax = plt.subplots(figsize=(20, 12))
    world.plot(ax=ax, color='#f5f5f5', edgecolor='#dddddd', linewidth=0.5)

    # True density hexbin
    x = airports_gdf.geometry.x
    y = airports_gdf.geometry.y

    hb = ax.hexbin(x, y, gridsize=80, cmap='inferno', mincnt=1)

    cb = plt.colorbar(hb, ax=ax, shrink=0.5)
    cb.set_label("Airport Density")

    plt.title('Global Airport Density by Size', fontsize=20)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('airport_heatmap.png', dpi=400, bbox_inches='tight')
    plt.show()


# Airports and ports proximity analysis

def airports_ports_proximity(buffer_km=50):
    """
    Identifying airports near major ports (multimodal hubs)
    """
    #Loading data
    airports = pd.read_csv(DATA_DIR / 'airports.csv')
    ports = gpd.read_file(DATA_DIR / 'ne_10m_ports.shp')
    world = gpd.read_file(DATA_DIR / 'ne_110m_admin_0_countries.shp')

    #Filtering for operational airports
    airports = airports[airports['type'].isin(['large_airport', 'medium_airport'])]
    geometry = [Point(xy) for xy in zip(airports['longitude_deg'], airports['latitude_deg'])]
    airports_gdf = gpd.GeoDataFrame(airports, geometry=geometry, crs='EPSG:4326')

    #Projecting to equal area for accurate buffering (meters)
    airports_proj = airports_gdf.to_crs('ESRI:54009')
    ports_proj = ports.to_crs('ESRI:54009')

    #Creating buffer around ports (convert km to meters)
    ports_buffered = ports_proj.buffer(buffer_km * 1000)

    #Finding airports within buffer
    ports_buffered_gdf = gpd.GeoDataFrame(geometry=ports_buffered, crs=ports_proj.crs)

    joined = gpd.sjoin(
        airports_proj,
        ports_buffered_gdf,
        predicate="within",
        how="left"
    )

    near_ids = joined.index.unique()
    airports_proj['near_port'] = airports_proj.index.isin(near_ids)

    #Converting back to WGS84 for plotting
    airports_gdf['near_port'] = airports_proj['near_port']


#Roads + Railways + Airports
def transportation_network_map(region_name='Europe', bbox=None):
    """
    Comprehensive transportation network visualization
    bbox format: [minx, miny, maxx, maxy]
    """
    #Loading data
    airports = pd.read_csv(DATA_DIR / 'airports.csv')
    world = gpd.read_file(DATA_DIR / 'ne_110m_admin_0_countries.shp')
    roads = gpd.read_file(DATA_DIR / 'ne_10m_roads.shp')
    railways = gpd.read_file(DATA_DIR / 'ne_10m_railroads.shp')

    roads = roads[roads['type'].isin(['Major Highway'])]

    #Filtering airports
    airports = airports[airports['type'].isin(['large_airport', 'medium_airport'])]
    geometry = [Point(xy) for xy in zip(airports['longitude_deg'], airports['latitude_deg'])]
    airports_gdf = gpd.GeoDataFrame(airports, geometry=geometry, crs='EPSG:4326')

    #Applying bounding box as specified
    if bbox:
        world = world.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
        airports_gdf = airports_gdf.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
        roads = roads.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
        railways = railways.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]

    #Plotting
    fig, ax = plt.subplots(figsize=(20, 16))
    world.plot(ax=ax, color='#f5f5f5', edgecolor='#dddddd', linewidth=0.5)

    #Plotting infrastructure layers
    roads.plot(ax=ax, color='#ff9999', linewidth=0.3, alpha=0.3, label='Major Roads')
    railways.plot(ax=ax, color='#333333', linewidth=0.4, alpha=0.4, label='Railways')

    #Plotting airports
    large = airports_gdf[airports_gdf['type'] == 'large_airport']
    medium = airports_gdf[airports_gdf['type'] == 'medium_airport']

    medium.plot(ax=ax, color='#E69F00', markersize=40, alpha=0.7,
                label='Medium Airports', zorder=3)
    large.plot(ax=ax, color='#C44E52', markersize=80, alpha=0.8,
               label='Large Airports', zorder=4)

    plt.title(f'Integrated Transportation Network: {region_name}',
              fontsize=20, fontweight='bold')
    plt.legend(loc='lower right', fontsize=12)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(f'transport_network_{region_name.lower()}.png', dpi=300, bbox_inches='tight')
    plt.show()

#Continental comparisons (SMALL MULTIPLES)

def continental_comparison():
    """
    Small multiples showing airport distribution by continent
    """
    airports = pd.read_csv(DATA_DIR / 'airports.csv')
    world = gpd.read_file(DATA_DIR / 'ne_110m_admin_0_countries.shp')

    airports = airports[airports['type'].isin(['large_airport', 'medium_airport', 'small_airport'])]
    geometry = [Point(xy) for xy in zip(airports['longitude_deg'], airports['latitude_deg'])]
    airports_gdf = gpd.GeoDataFrame(airports, geometry=geometry, crs='EPSG:4326')

    regions = {
        'North America': [-170, 15, -50, 75],
        'South America': [-85, -60, -30, 15],
        'Europe': [-15, 35, 45, 72],
        'Africa': [-20, -40, 55, 40],
        'Asia': [40, -10, 150, 55],
        'Oceania': [110, -50, 180, 0]
    }

    fig, axes = plt.subplots(2, 3, figsize=(24, 16))
    axes = axes.flatten()

    for idx, (region_name, bbox) in enumerate(regions.items()):
        ax = axes[idx]

        world_region = world.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
        airports_region = airports_gdf.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]

        world_region.plot(ax=ax, color='#f5f5f5', edgecolor='#dddddd', linewidth=0.5)

        for airport_type, color, size in [('small_airport', '#F0E442', 8),
                                          ('medium_airport', '#E69F00', 20),
                                          ('large_airport', '#C44E52', 40)]:
            subset = airports_region[airports_region['type'] == airport_type]
            if len(subset) > 0:
                subset.plot(ax=ax, color=color, markersize=size, alpha=0.7)

        ax.set_title(f'{region_name}\n{len(airports_region)} Airports',
                     fontsize=14)
        ax.set_xlim(bbox[0], bbox[2])
        ax.set_ylim(bbox[1], bbox[3])
        ax.axis('off')

    plt.suptitle('Continental Airport Distribution Patterns',
                 fontsize=20, y=0.98)
    plt.tight_layout()
    plt.savefig('continental_comparison.png', dpi=400, bbox_inches='tight')
    plt.show()


#Voronoi Diagrams

def airport_voronoi_diagram(region_bbox=None):
    """
    Creating Voronoi diagram showing airport service areas
    region_bbox format: [min_lon, min_lat, max_lon, max_lat]
    """

    #Loading data
    airports = pd.read_csv(DATA_DIR / 'airports.csv')
    world = gpd.read_file(DATA_DIR / 'ne_110m_admin_0_countries.shp')
    cities = gpd.read_file(DATA_DIR / 'ne_10m_populated_places.shp')

    #Filtering airports
    airports = airports[airports['type'].isin(['large_airport', 'medium_airport'])]

    geometry = [Point(xy) for xy in zip(airports['longitude_deg'], airports['latitude_deg'])]
    airports_gdf = gpd.GeoDataFrame(airports, geometry=geometry, crs="EPSG:4326")

    print("Airports remaining:", len(airports_gdf))

    #Applying bounding box BEFORE projection
    if region_bbox:
        minx, miny, maxx, maxy = region_bbox

        bbox_poly = gpd.GeoSeries(
            [Point(minx, miny).buffer(0)], crs="EPSG:4326"
        ).envelope

        airports_gdf = airports_gdf[
            (airports_gdf.geometry.x >= minx) &
            (airports_gdf.geometry.x <= maxx) &
            (airports_gdf.geometry.y >= miny) &
            (airports_gdf.geometry.y <= maxy)
        ]

        world = world.cx[minx:maxx, miny:maxy]
        cities = cities.cx[minx:maxx, miny:maxy]

    print("Airports remaining:", len(airports_gdf))

    #Safety check BEFORE projection (as fallback for checking airports)
    if len(airports_gdf) < 3:
        raise ValueError("Not enough airports inside bounding box for Voronoi.")

    #Projectin to equal-area
    airports_gdf = airports_gdf.to_crs("ESRI:54009")
    world = world.to_crs("ESRI:54009")
    cities = cities.to_crs("ESRI:54009")

    #Extracting coordinates
    coords = np.column_stack((airports_gdf.geometry.x, airports_gdf.geometry.y))

    #Voronoi
    vor = Voronoi(coords)

    #Plotting
    fig, ax = plt.subplots(figsize=(20, 16))

    world.plot(ax=ax, color='#f5f5f5', edgecolor='#dddddd', linewidth=0.5)
    minx, miny, maxx, maxy = world.total_bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    #Voronoi edges
    for simplex in vor.ridge_vertices:
        simplex = np.asarray(simplex)
        if np.all(simplex >= 0):
            ax.plot(
                vor.vertices[simplex, 0],
                vor.vertices[simplex, 1],
                linewidth=1,
                alpha=0.4,
                color="black"
            )

    cities.plot(ax=ax, color='gray', markersize=5, alpha=0.5, label='Cities')

    airports_gdf.plot(
        ax=ax,
        color='#C44E52',
        markersize=50,
        alpha=0.85,
        edgecolor='darkred',
        linewidth=1,
        label='Airports'
    )

    plt.title("Airport Service Areas (Voronoi Diagram)", fontsize=20)
    plt.legend(loc="lower right", frameon=False)
    plt.axis("off")

    plt.tight_layout()
    plt.savefig("airport_voronoi.png", dpi=400, bbox_inches="tight")
    plt.show()

#Deploying visualizations

if __name__ == "__main__":
    create_airport_heatmap()
    airports_ports_proximity(buffer_km=50)
    europe_bbox = [-15, 35, 45, 72]
    transportation_network_map('Europe', bbox=europe_bbox)
    continental_comparison()
    na_bbox = [-130, 25, -65, 50]
    airport_voronoi_diagram(region_bbox=na_bbox)
    pass