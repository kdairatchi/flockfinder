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
    
    # Check for environment variables first (for automated deployments)
    if os.environ.get('GITHUB_ACTIONS') == "true" or os.environ.get('CODESPACES') == "true":
        token = os.environ.get('WIGLE_TOKEN')
        if not token:
            print("Error: WIGLE_TOKEN environment variable not set")
            return False
    else:
        # Interactive token input
        token = getpass.getpass('Enter WiGLE API Token (Base64 encoded username:token): ')
        if not token:
            print("Error: No WiGLE API token provided")
            return False
    
    # Set up authentication header
    WIGLE_HEADER = {"Authorization": "Basic " + token}
    
    # Test authentication with a simple query
    try:
        test_response = requests.get(
            WIGLE_BASE_URL + '/api/v2/stats/site',
            headers=WIGLE_HEADER,
            timeout=REQUEST_TIMEOUT
        )
        
        if test_response.status_code == 200:
            print("WiGLE API authentication successful")
            return True
        elif test_response.status_code == 401:
            print("Error: Invalid WiGLE API credentials")
            return False
        else:
            print(f"Error: WiGLE API authentication failed with status {test_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not connect to WiGLE API: {e}")
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
        return None
    
    if params is None:
        params = {}
    
    url = WIGLE_BASE_URL + endpoint
    
    try:
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
        
        response = requests.get(
            url,
            headers=WIGLE_HEADER,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("Rate limited by WiGLE API. Waiting 60 seconds...")
            time.sleep(60)
            return make_wigle_request(endpoint, params)  # Retry once
        else:
            print(f"WiGLE API request failed: HTTP {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network error during WiGLE API request: {e}")
        return None


def search_by_coordinates(ssid_pattern: str, bounding_box: Dict[str, float]) -> List[Dict]:
    """
    Search WiGLE database by SSID pattern within coordinate boundaries
    
    Args:
        ssid_pattern (str): SSID pattern to search for
        bounding_box (dict): Geographic boundaries with north, south, east, west
        
    Returns:
        list: List of network records from WiGLE API
    """
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
    
    response = make_wigle_request(WIGLE_SEARCH_API, params)
    
    if response and response.get('success'):
        networks = response.get('results', [])
        return networks
    else:
        print(f"WiGLE search failed for pattern: {ssid_pattern}")
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
    filtered_networks = []
    
    for network in networks:
        bssid = network.get('netid', '')
        if len(bssid) >= 8:  # Ensure BSSID is long enough for prefix check
            bssid_prefix = bssid[:8]  # Get first 3 octets (XX:XX:XX format)
            if bssid_prefix.upper() in [prefix.upper() for prefix in bssid_prefixes]:
                filtered_networks.append(network)
    
    return filtered_networks


def add_wigle_metadata(networks: List[Dict]) -> None:
    """
    Add WiGLE-specific metadata to network records
    
    Args:
        networks (list): List of network records to enhance
    """
    for network in networks:
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
        return False
    
    try:
        lat_float = float(lat)
        lon_float = float(lon)
        
        # Basic coordinate bounds check
        if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
            return True
        else:
            return False
            
    except (ValueError, TypeError):
        return False


def clean_network_data(networks: List[Dict]) -> List[Dict]:
    """
    Clean and validate network data from WiGLE API
    
    Args:
        networks (list): Raw network records from WiGLE
        
    Returns:
        list: Cleaned and validated network records
    """
    cleaned_networks = []
    
    for network in networks:
        # Skip networks without valid coordinates
        if not validate_coordinates(network):
            continue
        
        # Skip networks without BSSID
        if not network.get('netid'):
            continue
        
        # Clean up empty or invalid fields
        cleaned_network = {}
        for key, value in network.items():
            if value is not None and value != '':
                cleaned_network[key] = value
        
        cleaned_networks.append(cleaned_network)
    
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
    all_networks = []
    
    for i, ssid_pattern in enumerate(ssid_patterns, 1):
        print(f"   Searching SSID pattern {i}/{len(ssid_patterns)}: {ssid_pattern}", end='\r')
        
        networks = search_by_coordinates(ssid_pattern, bounding_box)
        all_networks.extend(networks)
        
        # Rate limiting between requests
        time.sleep(RATE_LIMIT_DELAY)
    
    print(f"\nFound {len(all_networks)} total networks across all SSID patterns")
    
    # Remove duplicates based on BSSID
    unique_networks = {}
    for network in all_networks:
        bssid = network.get('netid')
        if bssid and bssid not in unique_networks:
            unique_networks[bssid] = network
    
    return list(unique_networks.values())


def get_api_quota_status() -> Optional[Dict]:
    """
    Check WiGLE API quota status
    
    Returns:
        dict: Quota information or None if unavailable
    """
    response = make_wigle_request('/api/v2/stats/user')
    
    if response and response.get('success'):
        user_stats = response.get('statistics', {})
        return {
            'daily_queries': user_stats.get('eventPrevCalendarDay', 0),
            'monthly_queries': user_stats.get('eventPrevMonth', 0),
            'total_queries': user_stats.get('discoveredGPS', 0)
        }
    else:
        return None