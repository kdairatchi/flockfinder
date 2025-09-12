"""
WiGLE API Integration
====================
Functions for authenticating with and querying the WiGLE.net database
for surveillance device WiFi signatures
"""

import getpass
import os
import requests
import time
from typing import Dict, List, Optional

from .config import DEBUG_MODE


def debug_print(*args, **kwargs):
    """Print debug message only if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        print("[DEBUG WIGLE]", *args, **kwargs)


# WiGLE API configuration
WIGLE_BASE_URL = 'https://api.wigle.net'
WIGLE_SEARCH_API = '/api/v2/network/search'
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0

# Global authentication header
WIGLE_HEADER = None


def authenticate_wigle() -> bool:
    """
    Authenticate with WiGLE API and set up global header
    
    Returns:
        bool: True if authentication successful, False otherwise
    """
    global WIGLE_HEADER
    debug_print("Starting WiGLE API authentication")
    
    # Check for environment variables first (for automated deployments)
    if os.environ.get('GITHUB_ACTIONS') == "true" or os.environ.get('CODESPACES') == "true":
        token = os.environ.get('WIGLE_TOKEN')
        debug_print("Using token from environment variable for automated deployment")
        if not token:
            print("Error: WIGLE_TOKEN environment variable not set")
            return False
    else:
        # Interactive token input
        debug_print("Prompting for interactive token input")
        token = getpass.getpass('Enter WiGLE API Token (Base64 encoded username:token): ')
        if not token:
            print("Error: No WiGLE API token provided")
            return False
    
    # Set up authentication header
    WIGLE_HEADER = {"Authorization": "Basic " + token}
    debug_print("Authentication header configured")
    
    # Test authentication with a simple query
    try:
        debug_print("Testing authentication with site stats query")
        test_response = requests.get(
            WIGLE_BASE_URL + '/api/v2/stats/site',
            headers=WIGLE_HEADER,
            timeout=REQUEST_TIMEOUT
        )
        
        debug_print(f"Auth test response: HTTP {test_response.status_code}")
        
        if test_response.status_code == 200:
            print("WiGLE API authentication successful")
            debug_print("Authentication test passed")
            return True
        elif test_response.status_code == 401:
            print("Error: Invalid WiGLE API credentials")
            debug_print("Authentication failed - invalid credentials")
            return False
        else:
            print(f"Error: WiGLE API authentication failed with status {test_response.status_code}")
            debug_print(f"Authentication failed with unexpected status: {test_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not connect to WiGLE API: {e}")
        debug_print(f"Network error during authentication: {e}")
        return False


def make_wigle_request(endpoint: str, params: Dict = None) -> Optional[Dict]:
    """
    Make authenticated request to WiGLE API with error handling
    
    Args:
        endpoint (str): API endpoint path
        params (dict): Query parameters
        
    Returns:
        dict: API response data or None if failed
    """
    if not WIGLE_HEADER:
        print("Error: WiGLE API not authenticated")
        debug_print("Request attempted without authentication")
        return None
    
    if params is None:
        params = {}
    
    url = WIGLE_BASE_URL + endpoint
    debug_print(f"Making WiGLE request to: {endpoint}")
    debug_print(f"Request parameters: {params}")
    
    try:
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
        debug_print(f"Applied rate limit delay: {RATE_LIMIT_DELAY}s")
        
        response = requests.get(
            url,
            headers=WIGLE_HEADER,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        
        debug_print(f"WiGLE API response: HTTP {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            debug_print(f"Response success: {response_data.get('success', 'unknown')}")
            if 'results' in response_data:
                debug_print(f"Results count: {len(response_data['results'])}")
            return response_data
        elif response.status_code == 429:
            print("Rate limited by WiGLE API. Waiting 60 seconds...")
            debug_print("Rate limit hit, waiting 60 seconds before retry")
            time.sleep(60)
            return make_wigle_request(endpoint, params)  # Retry once
        else:
            print(f"WiGLE API request failed: HTTP {response.status_code}")
            debug_print(f"Request failed, response text: {response.text[:200]}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network error during WiGLE API request: {e}")
        debug_print(f"Network error details: {e}")
        return None


def search_by_coordinates(ssid_pattern: str, bounding_box: Dict[str, float], state_code: str = None) -> List[Dict]:
    """
    Search WiGLE database by SSID pattern within coordinate boundaries
    
    Args:
        ssid_pattern (str): SSID pattern to search for
        bounding_box (dict): Geographic boundaries with north, south, east, west
        state_code (str): Optional state code for more precise filtering (e.g., 'TX', 'CA')
        
    Returns:
        list: List of network records from WiGLE API
    """
    debug_print(f"Searching for SSID pattern: {ssid_pattern}")
    debug_print(f"Bounding box: {bounding_box}")
    debug_print(f"State code: {state_code}")
    
    # Format bounding box for WiGLE API (latrange1,latrange2,longrange1,longrange2)
    params = {
        'ssidlike': ssid_pattern,
        'latrange1': bounding_box['south'],
        'latrange2': bounding_box['north'],
        'longrange1': bounding_box['west'],
        'longrange2': bounding_box['east'],
        'onlymine': 'false',
        'freenet': 'false',
        'paynet': 'false',
        'results': '100',  # Maximum results per request
        'lastupdt': '20200101'  # Only networks seen since 2020
    }
    
    # Add state parameter if provided for more precise filtering
    if state_code:
        params['state'] = state_code
        debug_print(f"Added state parameter: {state_code}")
    
    debug_print(f"WiGLE search parameters: {params}")
    
    response = make_wigle_request(WIGLE_SEARCH_API, params)
    
    if response and response.get('success'):
        networks = response.get('results', [])
        debug_print(f"Search successful: found {len(networks)} networks")
        return networks
    else:
        print(f"WiGLE search failed for pattern: {ssid_pattern}")
        debug_print(f"Search failed, response: {response}")
        return []


def filter_by_bssid_prefixes(networks: List[Dict], bssid_prefixes: List[str]) -> List[Dict]:
    """
    Filter network results by known BSSID prefixes
    
    Args:
        networks (list): List of network records from WiGLE
        bssid_prefixes (list): List of BSSID prefixes to match
        
    Returns:
        list: Filtered networks matching BSSID prefixes
    """
    debug_print(f"Filtering {len(networks)} networks by {len(bssid_prefixes)} BSSID prefixes")
    debug_print(f"BSSID prefixes: {bssid_prefixes}")
    
    filtered_networks = []
    
    for network in networks:
        bssid = network.get('netid', '')
        if len(bssid) >= 8:  # Ensure BSSID is long enough for prefix check
            bssid_prefix = bssid[:8]  # Get first 3 octets (XX:XX:XX format)
            debug_print(f"Checking BSSID: {bssid} (prefix: {bssid_prefix})")
            
            if bssid_prefix.upper() in [prefix.upper() for prefix in bssid_prefixes]:
                filtered_networks.append(network)
                debug_print(f"Match found: {bssid} matches known prefix")
            else:
                debug_print(f"No match: {bssid_prefix} not in known prefixes")
        else:
            debug_print(f"Skipping invalid BSSID: {bssid} (too short)")
    
    debug_print(f"Filtering complete: {len(filtered_networks)} networks matched")
    return filtered_networks


def add_wigle_metadata(networks: List[Dict]) -> None:
    """
    Add WiGLE-specific metadata to network records
    
    Args:
        networks (list): List of network records to enhance
    """
    debug_print(f"Adding WiGLE metadata to {len(networks)} networks")
    
    for i, network in enumerate(networks):
        bssid = network.get('netid', '')
        if bssid:
            # Add WiGLE map URL for each network
            network['wigle_map_url'] = f"https://wigle.net/search?netid={bssid}"
            
            # Add discovery source
            network['discovery_source'] = 'WiGLE.net'
            
            # Standardize coordinate field names if needed
            if 'trilat' in network and 'trilong' in network:
                network['latitude'] = network['trilat']
                network['longitude'] = network['trilong']
            
            debug_print(f"Enhanced network {i+1}: {bssid}")
    
    debug_print("WiGLE metadata addition complete")


def validate_coordinates(network: Dict) -> bool:
    """
    Validate that network has valid coordinate data
    
    Args:
        network (dict): Network record from WiGLE
        
    Returns:
        bool: True if coordinates are valid, False otherwise
    """
    lat = network.get('trilat') or network.get('latitude')
    lon = network.get('trilong') or network.get('longitude')
    
    if lat is None or lon is None:
        debug_print(f"Missing coordinates in network: {network.get('netid', 'unknown')}")
        return False
    
    try:
        lat_float = float(lat)
        lon_float = float(lon)
        
        # Basic coordinate bounds check
        if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
            debug_print(f"Valid coordinates: lat={lat_float}, lon={lon_float}")
            return True
        else:
            debug_print(f"Coordinates out of bounds: lat={lat_float}, lon={lon_float}")
            return False
            
    except (ValueError, TypeError) as e:
        debug_print(f"Coordinate conversion error: {e}")
        return False


def clean_network_data(networks: List[Dict]) -> List[Dict]:
    """
    Clean and validate network data from WiGLE API
    
    Args:
        networks (list): Raw network records from WiGLE
        
    Returns:
        list: Cleaned and validated network records
    """
    debug_print(f"Cleaning {len(networks)} network records")
    cleaned_networks = []
    
    for i, network in enumerate(networks):
        # Skip networks without valid coordinates
        if not validate_coordinates(network):
            debug_print(f"Skipping network {i+1}: invalid coordinates")
            continue
        
        # Skip networks without BSSID
        if not network.get('netid'):
            debug_print(f"Skipping network {i+1}: missing BSSID")
            continue
        
        # Clean up empty or invalid fields
        cleaned_network = {}
        for key, value in network.items():
            if value is not None and value != '':
                cleaned_network[key] = value
        
        cleaned_networks.append(cleaned_network)
        debug_print(f"Cleaned network {i+1}: {network.get('netid', 'unknown')}")
    
    debug_print(f"Cleaning complete: {len(cleaned_networks)} valid networks")
    return cleaned_networks


def search_multiple_ssids(ssid_patterns: List[str], bounding_box: Dict[str, float]) -> List[Dict]:
    """
    Search for multiple SSID patterns within geographic boundaries
    
    Args:
        ssid_patterns (list): List of SSID patterns to search for
        bounding_box (dict): Geographic boundaries
        
    Returns:
        list: Combined list of all network records found
    """
    debug_print(f"Searching {len(ssid_patterns)} SSID patterns")
    all_networks = []
    
    for i, ssid_pattern in enumerate(ssid_patterns, 1):
        print(f"   Searching SSID pattern {i}/{len(ssid_patterns)}: {ssid_pattern}", end='\r')
        debug_print(f"Processing SSID pattern {i}: {ssid_pattern}")
        
        networks = search_by_coordinates(ssid_pattern, bounding_box)
        all_networks.extend(networks)
        debug_print(f"Pattern {i} yielded {len(networks)} networks")
        
        # Rate limiting between requests
        time.sleep(RATE_LIMIT_DELAY)
    
    print(f"\nFound {len(all_networks)} total networks across all SSID patterns")
    debug_print(f"Total networks before deduplication: {len(all_networks)}")
    
    # Remove duplicates based on BSSID
    unique_networks = {}
    for network in all_networks:
        bssid = network.get('netid')
        if bssid and bssid not in unique_networks:
            unique_networks[bssid] = network
        elif bssid:
            debug_print(f"Duplicate BSSID found: {bssid}")
    
    final_networks = list(unique_networks.values())
    debug_print(f"After deduplication: {len(final_networks)} unique networks")
    return final_networks


def get_api_quota_status() -> Optional[Dict]:
    """
    Check WiGLE API quota status
    
    Returns:
        dict: Quota information or None if unavailable
    """
    debug_print("Checking WiGLE API quota status")
    response = make_wigle_request('/api/v2/stats/user')
    
    if response and response.get('success'):
        user_stats = response.get('statistics', {})
        quota_info = {
            'daily_queries': user_stats.get('eventPrevCalendarDay', 0),
            'monthly_queries': user_stats.get('eventPrevMonth', 0),
            'total_queries': user_stats.get('discoveredGPS', 0)
        }
        debug_print(f"Quota status: {quota_info}")
        return quota_info
    else:
        debug_print("Could not retrieve quota information")
        return None


def format_search_summary(networks: List[Dict], bssid_prefixes: List[str]) -> Dict:
    """
    Create formatted summary of search results
    
    Args:
        networks (list): Network records found
        bssid_prefixes (list): BSSID prefixes used in search
        
    Returns:
        dict: Formatted summary information
    """
    debug_print(f"Creating search summary for {len(networks)} networks")
    
    # Count matches by BSSID prefix
    prefix_matches = {}
    for prefix in bssid_prefixes:
        prefix_matches[prefix] = 0
    
    # Analyze network locations
    cities = {}
    ssids = {}
    
    for network in networks:
        # Count by BSSID prefix
        bssid = network.get('netid', '')
        if len(bssid) >= 8:
            bssid_prefix = bssid[:8].upper()
            for prefix in bssid_prefixes:
                if bssid_prefix == prefix.upper():
                    prefix_matches[prefix] += 1
                    break
        
        # Count by city
        city = network.get('city', 'Unknown')
        cities[city] = cities.get(city, 0) + 1
        
        # Count by SSID
        ssid = network.get('ssid', 'Unknown')
        ssids[ssid] = ssids.get(ssid, 0) + 1
    
    summary = {
        'total_networks': len(networks),
        'prefix_matches': prefix_matches,
        'cities': cities,
        'ssids': ssids,
        'unique_cities': len(cities),
        'unique_ssids': len(ssids)
    }
    
    debug_print(f"Search summary: {summary['total_networks']} networks, {summary['unique_cities']} cities, {summary['unique_ssids']} SSIDs")
    return summary