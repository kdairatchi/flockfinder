"""
OpenStreetMap Boundary Integration
=================================
Functions for querying OSM administrative boundaries via Overpass API
and calculating bounding boxes for geographic filtering
"""

import json
import os
import requests
import time
from typing import Dict, List, Optional, Tuple


# Overpass API configuration
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0


def get_cache_directory() -> str:
    """Get path to boundary cache directory"""
    package_dir = os.path.dirname(__file__)
    cache_dir = os.path.join(package_dir, '..', 'data')
    return os.path.normpath(cache_dir)


def ensure_cache_directory():
    """Ensure boundary cache directory exists"""
    cache_dir = get_cache_directory()
    os.makedirs(cache_dir, exist_ok=True)


def query_overpass(query: str) -> Optional[Dict]:
    """
    Execute Overpass API query with error handling and rate limiting
    
    Args:
        query (str): Overpass QL query string
        
    Returns:
        dict: API response data or None if failed
    """
    try:
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
        
        response = requests.post(
            OVERPASS_URL,
            data=query,
            headers={'Content-Type': 'text/plain; charset=utf-8'},
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("Rate limited by Overpass API. Waiting 60 seconds...")
            time.sleep(60)
            return query_overpass(query)  # Retry once
        else:
            print(f"Overpass API error: HTTP {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network error querying Overpass API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing Overpass API response: {e}")
        return None


def get_available_countries() -> Dict[str, str]:
    """
    Get list of available countries from OSM
    
    Returns:
        dict: Country code to country name mapping
    """
    # Check cache first
    cache_dir = get_cache_directory()
    cache_file = os.path.join(cache_dir, "countries.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                if cached_data.get('timestamp', 0) > time.time() - 86400:  # 24 hour cache
                    return cached_data.get('countries', {})
        except (json.JSONDecodeError, IOError):
            pass
    
    # Query Overpass API for countries
    query = """
    [out:json][timeout:25];
    (
      relation["admin_level"="2"]["boundary"="administrative"];
    );
    out tags;
    """
    
    print("Querying OpenStreetMap for available countries...")
    data = query_overpass(query)
    
    if not data or 'elements' not in data:
        print("Error: Could not retrieve country data from OpenStreetMap")
        return {}
    
    countries = {}
    for element in data['elements']:
        tags = element.get('tags', {})
        iso_code = tags.get('ISO3166-1:alpha2') or tags.get('country_code_iso3166_1_alpha_2')
        name = tags.get('name:en') or tags.get('name')
        
        if iso_code and name:
            countries[iso_code] = name
    
    # Cache the results
    ensure_cache_directory()
    cache_data = {
        'timestamp': time.time(),
        'countries': countries
    }
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except IOError:
        pass  # Cache write failure is not critical
    
    return countries


def get_admin_divisions(country_code: str, admin_level: int = 4) -> Dict[str, Dict]:
    """
    Get administrative divisions for a country from OSM
    
    Args:
        country_code (str): ISO country code (e.g., 'US', 'CA')
        admin_level (int): OSM admin level (4=states/provinces, 6=counties)
        
    Returns:
        dict: Administrative division code to data mapping
    """
    # Check cache first
    cache_dir = get_cache_directory()
    cache_file = os.path.join(cache_dir, f"{country_code}_admin_{admin_level}.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                if cached_data.get('timestamp', 0) > time.time() - 86400:  # 24 hour cache
                    return cached_data.get('divisions', {})
        except (json.JSONDecodeError, IOError):
            pass
    
    # Query Overpass API for administrative divisions
    query = f"""
    [out:json][timeout:25];
    (
      relation["admin_level"="{admin_level}"]["boundary"="administrative"]["ISO3166-1:alpha2"="{country_code}"];
    );
    out geom tags;
    """
    
    print(f"Querying OpenStreetMap for {country_code} administrative divisions...")
    data = query_overpass(query)
    
    if not data or 'elements' not in data:
        print(f"Error: Could not retrieve administrative divisions for {country_code}")
        return {}
    
    divisions = {}
    for element in data['elements']:
        tags = element.get('tags', {})
        geometry = element.get('members', [])
        
        # Extract division information
        admin_code = (tags.get('ref') or 
                     tags.get('ISO3166-2') or 
                     tags.get('state_code') or 
                     tags.get('fips_code') or
                     str(element.get('id', '')))
        
        name = tags.get('name:en') or tags.get('name') or admin_code
        
        if admin_code:
            # Extract coordinates from geometry
            coordinates = extract_coordinates_from_geometry(geometry)
            
            divisions[admin_code] = {
                'name': name,
                'osm_id': element.get('id'),
                'tags': tags,
                'coordinates': coordinates,
                'admin_level': admin_level
            }
    
    # Cache the results
    ensure_cache_directory()
    cache_data = {
        'timestamp': time.time(),
        'country_code': country_code,
        'admin_level': admin_level,
        'divisions': divisions
    }
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except IOError:
        pass  # Cache write failure is not critical
    
    return divisions


def extract_coordinates_from_geometry(members: List[Dict]) -> List[Tuple[float, float]]:
    """
    Extract coordinate pairs from OSM relation geometry
    
    Args:
        members (list): OSM relation members with geometry
        
    Returns:
        list: List of (longitude, latitude) coordinate tuples
    """
    coordinates = []
    
    for member in members:
        if member.get('type') == 'way' and 'geometry' in member:
            for node in member['geometry']:
                lon = node.get('lon')
                lat = node.get('lat')
                if lon is not None and lat is not None:
                    coordinates.append((lon, lat))
    
    return coordinates


def calculate_bounding_box(coordinates: List[Tuple[float, float]]) -> Optional[Dict[str, float]]:
    """
    Calculate bounding box from list of coordinates using pure Python
    
    Args:
        coordinates (list): List of (longitude, latitude) tuples
        
    Returns:
        dict: Bounding box with north, south, east, west bounds or None if empty
    """
    if not coordinates:
        return None
    
    lons = [coord[0] for coord in coordinates]
    lats = [coord[1] for coord in coordinates]
    
    return {
        'west': min(lons),
        'east': max(lons),
        'south': min(lats),
        'north': max(lats)
    }


def cache_boundary_data(country_code: str, boundary_data: Dict) -> None:
    """
    Cache boundary data for offline use
    
    Args:
        country_code (str): ISO country code
        boundary_data (dict): Boundary data to cache
    """
    ensure_cache_directory()
    cache_dir = get_cache_directory()
    cache_file = os.path.join(cache_dir, f"{country_code}_boundaries.json")
    
    cache_data = {
        'timestamp': time.time(),
        'country_code': country_code,
        'boundaries': boundary_data
    }
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        print(f"Cached boundary data for {country_code}")
    except IOError as e:
        print(f"Warning: Could not cache boundary data: {e}")


def validate_bounding_box(bbox: Dict[str, float]) -> bool:
    """
    Validate bounding box coordinates
    
    Args:
        bbox (dict): Bounding box with north, south, east, west keys
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_keys = ['north', 'south', 'east', 'west']
    
    if not all(key in bbox for key in required_keys):
        return False
    
    # Basic coordinate validation
    if bbox['north'] <= bbox['south']:
        return False
    if bbox['east'] <= bbox['west']:
        return False
    
    # Latitude bounds check
    if bbox['north'] > 90 or bbox['south'] < -90:
        return False
    
    # Longitude bounds check (allow for crossing antimeridian)
    if bbox['east'] > 180 or bbox['west'] < -180:
        return False
    
    return True


def clear_boundary_cache(country_code: str = None) -> None:
    """
    Clear cached boundary data
    
    Args:
        country_code (str): Specific country to clear, or None for all
    """
    cache_dir = get_cache_directory()
    if not os.path.exists(cache_dir):
        return
    
    if country_code:
        # Clear specific country cache
        cache_files = [
            f"{country_code}_admin_4.json",
            f"{country_code}_admin_6.json",
            f"{country_code}_boundaries.json"
        ]
    else:
        # Clear all cache files
        cache_files = os.listdir(cache_dir)
    
    for filename in cache_files:
        cache_file = os.path.join(cache_dir, filename)
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
                print(f"Cleared cache: {filename}")
        except OSError as e:
            print(f"Warning: Could not clear cache file {filename}: {e}")