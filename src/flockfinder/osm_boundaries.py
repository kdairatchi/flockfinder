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

from .config import DEBUG_MODE


def debug_print(*args, **kwargs):
    """Print debug message only if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        print("[DEBUG OSM]", *args, **kwargs)


# Overpass API configuration
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0


def get_cache_directory() -> str:
    """Get path to boundary cache directory"""
    package_dir = os.path.dirname(__file__)
    cache_dir = os.path.join(package_dir, '..', '..', 'data')
    return os.path.normpath(cache_dir)


def ensure_cache_directory():
    """Ensure boundary cache directory exists"""
    cache_dir = get_cache_directory()
    os.makedirs(cache_dir, exist_ok=True)
    debug_print(f"Cache directory ensured: {cache_dir}")


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
        debug_print(f"Executing Overpass query with {RATE_LIMIT_DELAY}s delay")
        
        response = requests.post(
            OVERPASS_URL,
            data=query,
            headers={'Content-Type': 'text/plain; charset=utf-8'},
            timeout=REQUEST_TIMEOUT
        )
        
        debug_print(f"Overpass API response: HTTP {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("Rate limited by Overpass API. Waiting 60 seconds...")
            debug_print("Rate limit hit, waiting 60 seconds before retry")
            time.sleep(60)
            return query_overpass(query)  # Retry once
        else:
            print(f"Overpass API error: HTTP {response.status_code}")
            debug_print(f"Overpass API error details: {response.text[:200]}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network error querying Overpass API: {e}")
        debug_print(f"Network error details: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing Overpass API response: {e}")
        debug_print(f"JSON decode error: {e}")
        return None


def get_available_countries() -> Dict[str, str]:
    """
    Get list of available countries from OSM
    
    Returns:
        dict: Country code to country name mapping
    """
    debug_print("Getting available countries from OSM")
    
    # Check cache first
    cache_dir = get_cache_directory()
    cache_file = os.path.join(cache_dir, "countries.json")
    
    debug_print(f"Checking cache file: {cache_file}")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                cache_age = time.time() - cached_data.get('timestamp', 0)
                debug_print(f"Cache file age: {cache_age/3600:.1f} hours")
                
                if cached_data.get('timestamp', 0) > time.time() - 86400:  # 24 hour cache
                    countries = cached_data.get('countries', {})
                    debug_print(f"Using cached countries data: {len(countries)} countries")
                    return countries
                else:
                    debug_print("Cache expired, will query fresh data")
        except (json.JSONDecodeError, IOError) as e:
            debug_print(f"Cache read error: {e}")
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
    debug_print("Executing countries query")
    data = query_overpass(query)
    
    if not data or 'elements' not in data:
        print("Error: Could not retrieve country data from OpenStreetMap")
        debug_print("No data or elements in response")
        return {}
    
    debug_print(f"Received {len(data.get('elements', []))} country elements")
    
    countries = {}
    for element in data['elements']:
        tags = element.get('tags', {})
        iso_code = tags.get('ISO3166-1:alpha2') or tags.get('country_code_iso3166_1_alpha_2')
        name = tags.get('name:en') or tags.get('name')
        
        if iso_code and name:
            countries[iso_code] = name
            debug_print(f"Added country: {iso_code} -> {name}")
    
    debug_print(f"Final countries count: {len(countries)}")
    
    # Cache the results
    ensure_cache_directory()
    cache_data = {
        'timestamp': time.time(),
        'countries': countries
    }
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        debug_print(f"Cached countries data to {cache_file}")
    except IOError as e:
        debug_print(f"Cache write failed: {e}")
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
    debug_print(f"Extracting coordinates from {len(members)} geometry members")
    coordinates = []
    
    for i, member in enumerate(members):
        debug_print(f"Processing member {i}: type={member.get('type')}, keys={list(member.keys())}")
        
        if member.get('type') == 'way' and 'geometry' in member:
            geometry = member['geometry']
            debug_print(f"Way geometry has {len(geometry)} nodes")
            
            for j, node in enumerate(geometry):
                lon = node.get('lon')
                lat = node.get('lat')
                if lon is not None and lat is not None:
                    coordinates.append((lon, lat))
                    # Only debug first few coordinates to avoid spam
                    if j < 3:
                        debug_print(f"Node {j}: lon={lon}, lat={lat}")
                else:
                    if j < 3:  # Only debug first few missing nodes
                        debug_print(f"Node {j}: missing lon/lat - keys={list(node.keys())}")
                    
                # Limit debug output for large geometries
                if j > 10 and DEBUG_MODE:
                    if j == 11:  # Only print this message once
                        debug_print(f"... (truncating debug output, total nodes: {len(geometry)})")
                    break
        else:
            debug_print(f"Skipping member {i}: not a way with geometry")
    
    debug_print(f"Extracted {len(coordinates)} total coordinate pairs")
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
    debug_print(f"Getting admin divisions for {country_code}, level {admin_level}")
    
    # Supported countries with tested queries
    SUPPORTED_COUNTRIES = ['US']  # Add more as we test them
    
    if country_code not in SUPPORTED_COUNTRIES:
        print(f"Error: Country '{country_code}' is not yet supported.")
        print(f"Currently supported: {', '.join(SUPPORTED_COUNTRIES)}")
        debug_print(f"Unsupported country requested: {country_code}")
        return {}
    
    debug_print(f"{country_code} is supported, continuing...")
    
    # Check cache first
    cache_dir = get_cache_directory()
    cache_file = os.path.join(cache_dir, f"{country_code}_admin_{admin_level}.json")
    
    debug_print(f"Checking cache file: {cache_file}")
    debug_print(f"Cache file exists: {os.path.exists(cache_file)}")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                cache_age = time.time() - cached_data.get('timestamp', 0)
                debug_print(f"Cache age: {cache_age/3600:.1f} hours")
                
                if cached_data.get('timestamp', 0) > time.time() - 86400:  # 24 hour cache
                    divisions = cached_data.get('divisions', {})
                    debug_print(f"Using cached data with {len(divisions)} divisions")
                    return divisions
                else:
                    debug_print("Cache expired, will query fresh data")
        except (json.JSONDecodeError, IOError) as e:
            debug_print(f"Cache read error: {e}")
            pass
    
    debug_print("No valid cache found, querying OSM...")
    
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
        debug_print(f"Using US query for admin_level {admin_level}")
    else:
        print(f"Error: Query not implemented for country '{country_code}'")
        debug_print(f"No query implementation for {country_code}")
        return {}
    
    print(f"Querying OpenStreetMap for {country_code} administrative divisions...")
    data = query_overpass(query)
    
    # Debug response
    debug_print(f"Query returned data: {data is not None}")
    if data:
        elements = data.get('elements', [])
        debug_print(f"Elements in response: {len(elements)}")
        if elements:
            debug_print(f"First element keys: {list(elements[0].keys())}")
            first_name = elements[0].get('tags', {}).get('name')
            debug_print(f"First element name: {first_name}")
        else:
            debug_print("No elements in response")
    else:
        debug_print("No data returned from query")
    
    if not data or 'elements' not in data:
        print(f"Error: Could not retrieve administrative divisions for {country_code}")
        return {}
    
    print(f"Found {len(data.get('elements', []))} administrative divisions")
    
    divisions = {}
    for i, element in enumerate(data['elements']):
        tags = element.get('tags', {})
        geometry = element.get('members', [])
        
        element_name = tags.get('name', 'Unknown')
        debug_print(f"Processing element {i+1}: {element_name}")
        debug_print(f"Element has {len(geometry)} geometry members")
        
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
        
        debug_print(f"Extracted admin_code='{admin_code}', name='{name}'")
        
        if admin_code and name:
            # Extract coordinates from geometry
            debug_print(f"Extracting coordinates for {name}")
            coordinates = extract_coordinates_from_geometry(geometry)
            debug_print(f"Extracted {len(coordinates)} coordinates for {name}")
            
            divisions[admin_code] = {
                'name': name,
                'osm_id': element.get('id'),
                'tags': tags,
                'coordinates': coordinates,
                'admin_level': admin_level
            }
            debug_print(f"Added division: {admin_code} - {name} with {len(coordinates)} coords")
        else:
            debug_print(f"Skipped element - missing admin_code or name")
    
    debug_print(f"Final divisions count: {len(divisions)}")
    
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
        debug_print(f"Cached {len(divisions)} divisions to {cache_file}")
    except IOError as e:
        debug_print(f"Cache write failed: {e}")
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
        debug_print("No coordinates provided for bounding box calculation")
        return None
    
    debug_print(f"Calculating bounding box from {len(coordinates)} coordinates")
    
    lons = [coord[0] for coord in coordinates]
    lats = [coord[1] for coord in coordinates]
    
    bounding_box = {
        'west': min(lons),
        'east': max(lons),
        'south': min(lats),
        'north': max(lats)
    }
    
    debug_print(f"Calculated bounding box: {bounding_box}")
    return bounding_box


def cache_boundary_data(country_code: str, boundary_data: Dict) -> None:
    """
    Cache boundary data for offline use
    
    Args:
        country_code (str): ISO country code
        boundary_data (dict): Boundary data to cache
    """
    debug_print(f"Caching boundary data for {country_code}")
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
        debug_print(f"Boundary data cached to {cache_file}")
    except IOError as e:
        print(f"Warning: Could not cache boundary data: {e}")
        debug_print(f"Cache write error: {e}")


def validate_bounding_box(bbox: Dict[str, float]) -> bool:
    """
    Validate bounding box coordinates
    
    Args:
        bbox (dict): Bounding box with north, south, east, west keys
        
    Returns:
        bool: True if valid, False otherwise
    """
    debug_print(f"Validating bounding box: {bbox}")
    required_keys = ['north', 'south', 'east', 'west']
    
    if not all(key in bbox for key in required_keys):
        debug_print(f"Missing required keys. Required: {required_keys}, Found: {list(bbox.keys())}")
        return False
    
    # Basic coordinate validation
    if bbox['north'] <= bbox['south']:
        debug_print(f"Invalid latitude range: north({bbox['north']}) <= south({bbox['south']})")
        return False
    if bbox['east'] <= bbox['west']:
        debug_print(f"Invalid longitude range: east({bbox['east']}) <= west({bbox['west']})")
        return False
    
    # Latitude bounds check
    if bbox['north'] > 90 or bbox['south'] < -90:
        debug_print(f"Latitude out of bounds: north={bbox['north']}, south={bbox['south']}")
        return False
    
    # Longitude bounds check (allow for crossing antimeridian)
    if bbox['east'] > 180 or bbox['west'] < -180:
        debug_print(f"Longitude out of bounds: east={bbox['east']}, west={bbox['west']}")
        return False
    
    debug_print("Bounding box validation passed")
    return True


def clear_boundary_cache(country_code: str = None) -> None:
    """
    Clear cached boundary data
    
    Args:
        country_code (str): Specific country to clear, or None for all
    """
    debug_print(f"Clearing boundary cache for: {country_code or 'all countries'}")
    cache_dir = get_cache_directory()
    if not os.path.exists(cache_dir):
        debug_print("Cache directory does not exist")
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
                debug_print(f"Removed cache file: {cache_file}")
        except OSError as e:
            print(f"Warning: Could not clear cache file {filename}: {e}")
            debug_print(f"Cache removal error: {e}")


def get_cache_info() -> Dict:
    """
    Get information about cached boundary data
    
    Returns:
        dict: Cache information including file sizes and timestamps
    """
    debug_print("Getting cache information")
    cache_dir = get_cache_directory()
    cache_info = {
        'cache_directory': cache_dir,
        'cache_exists': os.path.exists(cache_dir),
        'files': []
    }
    
    if not cache_info['cache_exists']:
        debug_print("Cache directory does not exist")
        return cache_info
    
    try:
        for filename in os.listdir(cache_dir):
            file_path = os.path.join(cache_dir, filename)
            if os.path.isfile(file_path) and filename.endswith('.json'):
                stat = os.stat(file_path)
                file_info = {
                    'filename': filename,
                    'size_bytes': stat.st_size,
                    'modified_timestamp': stat.st_mtime,
                    'age_hours': (time.time() - stat.st_mtime) / 3600
                }
                cache_info['files'].append(file_info)
                debug_print(f"Cache file: {filename}, size: {stat.st_size} bytes, age: {file_info['age_hours']:.1f}h")
    except OSError as e:
        debug_print(f"Error reading cache directory: {e}")
    
    return cache_info