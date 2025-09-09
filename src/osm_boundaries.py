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


def extract_coordinates_from_geometry(members: List[Dict]) -> List[Tuple[float, float]]:
    """
    Extract coordinate pairs from OSM relation geometry
    
    Args:
        members (list): OSM relation members with geometry
        
    Returns:
        list: List of (longitude, latitude) coordinate tuples
    """
    print(f"DEBUG COORDS: extract_coordinates_from_geometry called with {len(members)} members")
    coordinates = []
    
    for i, member in enumerate(members):
        print(f"DEBUG COORDS: Member {i}: type={member.get('type')}, keys={list(member.keys())}")
        
        if member.get('type') == 'way' and 'geometry' in member:
            geometry = member['geometry']
            print(f"DEBUG COORDS: Way geometry has {len(geometry)} nodes")
            
            for j, node in enumerate(geometry):
                lon = node.get('lon')
                lat = node.get('lat')
                if lon is not None and lat is not None:
                    coordinates.append((lon, lat))
                    if j < 3:  # Only print first few for debugging
                        print(f"DEBUG COORDS: Node {j}: lon={lon}, lat={lat}")
                else:
                    print(f"DEBUG COORDS: Node {j}: missing lon/lat - keys={list(node.keys())}")
                    
                if j > 10:  # Don't spam too much debug
                    break
        else:
            print(f"DEBUG COORDS: Skipping member {i}: not a way with geometry")
    
    print(f"DEBUG COORDS: Final extracted {len(coordinates)} coordinate pairs")
    return coordinates


def get_admin_divisions(country_code: str, admin_level: int = 4) -> Dict[str, Dict]:
    """
    Get administrative divisions for a country from OSM
    
    Args:
        country_code (str): ISO country code (e.g., 'US', 'CA')
        admin_level (int): OSM admin level (4=states/provinces, 6=counties)
        
    Returns:
        dict: Administrative division code to data mapping
    """
    print("DEBUG OSM: get_admin_divisions called - VERSION 2")  # ADD THIS LINE
    print(f"DEBUG OSM: Starting get_admin_divisions for {country_code}")
    
    # Supported countries with tested queries
    SUPPORTED_COUNTRIES = ['US']  # Add more as we test them
    
    if country_code not in SUPPORTED_COUNTRIES:
        print(f"Error: Country '{country_code}' is not yet supported.")
        print(f"Currently supported: {', '.join(SUPPORTED_COUNTRIES)}")
        return {}
    
    print(f"DEBUG OSM: {country_code} is supported, continuing...")
    
    # Check cache first
    cache_dir = get_cache_directory()
    cache_file = os.path.join(cache_dir, f"{country_code}_admin_{admin_level}.json")
    
    print(f"DEBUG OSM: Looking for cache file: {cache_file}")
    print(f"DEBUG OSM: Cache file exists: {os.path.exists(cache_file)}")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                cache_age = time.time() - cached_data.get('timestamp', 0)
                print(f"DEBUG OSM: Cache age: {cache_age/3600:.1f} hours")
                if cached_data.get('timestamp', 0) > time.time() - 86400:  # 24 hour cache
                    divisions = cached_data.get('divisions', {})
                    print(f"DEBUG OSM: Using cached data with {len(divisions)} divisions")
                    return divisions
                else:
                    print("DEBUG OSM: Cache expired, will query fresh")
        except (json.JSONDecodeError, IOError):
            print("DEBUG OSM: Cache file exists but couldn't be read")
            pass
    
    print("DEBUG OSM: No valid cache found, querying OSM...")
    
    # Build query based on country
    if country_code == "US":
        # US-specific query using ISO3166-2 codes
        query = f"""
        [out:json][timeout:25];
        (
        relation["admin_level"="{admin_level}"]["boundary"="administrative"]["ISO3166-2"~"^US-"];
        );
        out geom;
        """
        print(f"DEBUG OSM: Using US query for admin_level {admin_level}")
    else:
        print(f"Error: Query not implemented for country '{country_code}'")
        return {}
    
    print(f"Querying OpenStreetMap for {country_code} administrative divisions...")
    data = query_overpass(query)
    
    # DEBUG OUTPUT
    print(f"DEBUG OSM: Query returned data: {data is not None}")
    if data:
        elements = data.get('elements', [])
        print(f"DEBUG OSM: Elements in response: {len(elements)}")
        if elements:
            print(f"DEBUG OSM: First element has keys: {list(elements[0].keys())}")
            print(f"DEBUG OSM: First element tags: {elements[0].get('tags', {}).get('name')}")
        else:
            print("DEBUG OSM: No elements in response")
    else:
        print("DEBUG OSM: No data returned from query")
    
    if not data or 'elements' not in data:
        print(f"Error: Could not retrieve administrative divisions for {country_code}")
        return {}
    
    print(f"Found {len(data.get('elements', []))} administrative divisions")
    
    divisions = {}
    for i, element in enumerate(data['elements']):
        tags = element.get('tags', {})
        geometry = element.get('members', [])
        
        element_name = tags.get('name', 'Unknown')
        print(f"DEBUG OSM: Processing element {i+1}: {element_name}")
        print(f"DEBUG OSM: Element has {len(geometry)} geometry members")
        
        # Extract division information - US specific handling
        if country_code == "US":
            # For US, get the state code from ISO3166-2 (e.g., "US-TX" -> "TX")
            iso_code = tags.get('ISO3166-2', '')
            admin_code = iso_code.replace('US-', '') if iso_code.startswith('US-') else (
                tags.get('ref') or 
                tags.get('ref:USPS') or
                str(element.get('id', ''))
            )
        else:
            admin_code = (tags.get('ref') or 
                         tags.get('ISO3166-2') or 
                         tags.get('state_code') or 
                         tags.get('fips_code') or
                         str(element.get('id', '')))
        
        name = tags.get('name:en') or tags.get('name') or admin_code
        
        print(f"DEBUG OSM: Extracted admin_code='{admin_code}', name='{name}'")
        
        if admin_code and name:
            # Extract coordinates from geometry
            print(f"DEBUG OSM: About to extract coordinates for {name}")
            coordinates = extract_coordinates_from_geometry(geometry)
            print(f"DEBUG OSM: Extracted {len(coordinates)} coordinates for {name}")
            
            divisions[admin_code] = {
                'name': name,
                'osm_id': element.get('id'),
                'tags': tags,
                'coordinates': coordinates,
                'admin_level': admin_level
            }
            print(f"DEBUG OSM: Added division: {admin_code} - {name} with {len(coordinates)} coords")
        else:
            print(f"DEBUG OSM: Skipped element - missing admin_code or name")
    
    print(f"DEBUG OSM: Final divisions count: {len(divisions)}")
    
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
        print(f"DEBUG OSM: Cached {len(divisions)} divisions to {cache_file}")
    except IOError as e:
        print(f"DEBUG OSM: Cache write failed: {e}")
        pass  # Cache write failure is not critical
    
    return divisions


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