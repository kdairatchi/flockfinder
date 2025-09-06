#!/usr/bin/env python3
"""
FlockFinder - ALPR Surveillance Camera Detection
===============================================
Modular script with geographic region selection and external data files
Outputs JSON, universal CSV, and KML formats for mapping platforms
"""

### IMPORTS ###
import csv
import getpass
import json
import os
import requests
import sys
import time

### GLOBALS ###
## Wigle API Authentication
if os.environ.get('GITHUB_ACTIONS') == "true" or os.environ.get('CODESPACES') == "true":
    TOKEN = os.environ.get('WIGLE_TOKEN')
else:
    TOKEN = getpass.getpass('Enter Wigle API Token: ')

HEADER = {"Authorization": "Basic " + TOKEN}
BASEURL = 'https://api.wigle.net'
API = '/api/v2/network/search'

# Data loaded from external JSON files
BSSIDS = []      # Will be populated from known_bssid_prefixes.json
SSIDS = []       # Will be populated from known_ssid_prefixes.json
ZIPCODES = {}    # Will be populated from selected county files

### FUNCTIONS ###

def load_bssid_prefixes(filename="known_bssid_prefixes.json"):
    """
    Load known BSSID prefixes from external JSON file
    
    Args:
        filename (str): JSON file containing BSSID prefixes
        
    Returns:
        list: List of BSSID prefixes (first 3 octets)
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                bssid_list = data.get('bssid_prefixes', [])
                
                if not bssid_list:
                    print(f"No BSSID prefixes found in {filename}")
                    print(f"Please add BSSID prefixes to the 'bssid_prefixes' array in the file")
                    return []
                
                print(f"Loaded {len(bssid_list)} BSSID prefixes from {filename}")
                return bssid_list
        else:
            print(f"Required file not found: {filename}")
            print(f"Please create {filename} with known surveillance device BSSID prefixes")
            print(f"See documentation for the correct JSON format")
            return []
            
    except json.JSONDecodeError as e:
        print(f"Error parsing {filename}: {e}")
        print(f"Please check the JSON format in {filename}")
        return []
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return []

def load_ssid_prefixes(filename="known_ssid_prefixes.json"):
    """
    Load known SSID prefixes from external JSON file
    
    Args:
        filename (str): JSON file containing SSID prefixes
        
    Returns:
        list: List of SSID prefixes with wildcards
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ssid_list = data.get('ssid_prefixes', [])
                
                if not ssid_list:
                    print(f"No SSID prefixes found in {filename}")
                    print(f"Please add SSID prefixes to the 'ssid_prefixes' array in the file")
                    return []
                
                print(f"Loaded {len(ssid_list)} SSID prefixes from {filename}")
                return ssid_list
        else:
            print(f"Required file not found: {filename}")
            print(f"Please create {filename} with known surveillance device SSID prefixes")
            print(f"See documentation for the correct JSON format")
            return []
            
    except json.JSONDecodeError as e:
        print(f"Error parsing {filename}: {e}")
        print(f"Please check the JSON format in {filename}")
        return []
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return []

def load_geographic_registry(filename="geographic_registry.json"):
    """
    Load the geographic registry containing available states and counties
    
    Args:
        filename (str): Geographic registry JSON file
        
    Returns:
        dict: Geographic registry data
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Geographic registry not found: {filename}")
            print("Please create the geographic registry file. See documentation for format.")
            return None
    except Exception as e:
        print(f"Error loading geographic registry: {e}")
        return None

def load_county_zipcode_data(file_path):
    """
    Load ZIP code data from a county-specific JSON file
    
    Args:
        file_path (str): Path to county ZIP code JSON file
        
    Returns:
        dict: ZIP code data with city/county mappings
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                county_data = json.load(f)
                zip_dict = {}
                county_name = county_data.get('county', 'Unknown')
                
                # Convert county JSON format to our internal format
                for zip_code, zip_info in county_data.get('zip_codes', {}).items():
                    zip_dict[zip_code] = {
                        'city': zip_info.get('city', 'Unknown'),
                        'county': county_name
                    }
                
                print(f"Loaded {len(zip_dict)} ZIP codes from {county_name} County")
                return zip_dict
        else:
            print(f"County file not found: {file_path}")
            return {}
    except Exception as e:
        print(f"Error loading county data from {file_path}: {e}")
        return {}

def select_geographic_regions():
    """
    Interactive geographic region selection interface
    
    Returns:
        tuple: (combined ZIP code dictionary, state_code for API)
    """
    print("\n" + "="*60)
    print("GEOGRAPHIC REGION SELECTION")
    print("="*60)
    
    # Load geographic registry
    registry = load_geographic_registry()
    if not registry:
        print("Cannot load geographic registry.")
        return {}, None
    
    available_regions = registry.get('available_regions', {})
    if not available_regions:
        print("No geographic regions available in registry.")
        return {}, None
    
    # Step 1: Select State
    print("\nAvailable States:")
    states = sorted(available_regions.keys())
    for i, state in enumerate(states, 1):
        state_info = available_regions[state]
        county_count = len(state_info.get('counties', {}))
        print(f"  {i}. {state} ({state_info.get('state_code', 'N/A')}) - {county_count} counties")
    
    while True:
        try:
            state_choice = input(f"\nSelect state (1-{len(states)}) or 'q' to quit: ").strip()
            if state_choice.lower() == 'q':
                print("Exiting...")
                sys.exit(0)
            
            state_idx = int(state_choice) - 1
            if 0 <= state_idx < len(states):
                selected_state = states[state_idx]
                break
            else:
                print(f"Please enter a number between 1 and {len(states)}")
        except ValueError:
            print("Please enter a valid number or 'q' to quit")
    
    print(f"\nSelected state: {selected_state}")
    
    # Get state code for API
    state_data = available_regions[selected_state]
    state_code = state_data.get('state_code', 'TX')
    
    # Step 2: Select Counties
    counties = sorted(state_data.get('counties', {}).keys())
    
    print(f"\nAvailable Counties in {selected_state}:")
    for i, county in enumerate(counties, 1):
        county_info = state_data['counties'][county]
        zip_count = county_info.get('zip_count', 0)
        major_cities = ", ".join(county_info.get('major_cities', [])[:3])
        print(f"  {i}. {county} County - {zip_count} ZIP codes ({major_cities})")
    
    print(f"\n  {len(counties) + 1}. All counties (entire state)")
    
    while True:
        try:
            county_input = input(f"\nSelect counties (1-{len(counties) + 1}), multiple separated by commas, or 'q' to quit: ").strip()
            if county_input.lower() == 'q':
                print("Exiting...")
                sys.exit(0)
            
            # Handle "all counties" selection
            if county_input == str(len(counties) + 1):
                selected_counties = counties
                break
            
            # Handle multiple county selection
            county_choices = [int(x.strip()) - 1 for x in county_input.split(',')]
            selected_counties = []
            
            for choice in county_choices:
                if 0 <= choice < len(counties):
                    selected_counties.append(counties[choice])
                else:
                    raise ValueError(f"Invalid county selection: {choice + 1}")
            
            if selected_counties:
                break
            else:
                print("No valid counties selected")
                
        except ValueError as e:
            print(f"{e}. Please enter valid numbers separated by commas")
    
    print(f"\nSelected counties: {', '.join(selected_counties)}")
    
    # Step 3: Load ZIP code data from selected counties
    print(f"\nLoading ZIP code data...")
    combined_zipcodes = {}
    
    for county in selected_counties:
        county_info = state_data['counties'][county]
        file_path = county_info.get('file', '')
        
        if file_path:
            county_zips = load_county_zipcode_data(file_path)
            combined_zipcodes.update(county_zips)
        else:
            print(f"No file path specified for {county} County")
    
    print(f"\nTotal ZIP codes loaded: {len(combined_zipcodes)}")
    print(f"Coverage: {', '.join(selected_counties)} County/Counties, {selected_state}")
    
    return combined_zipcodes, state_code

def make_wigle_request(endpoint, params=None):
    """Make WiGLE API request with minimal output"""
    if params is None:
        params = {}
    
    url = BASEURL + endpoint
    
    try:
        response = requests.get(url, headers=HEADER, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("Rate limited by WiGLE API. Waiting 60 seconds...")
            time.sleep(60)
            return make_wigle_request(endpoint, params)
        else:
            print(f"API request failed: HTTP {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None

def search_by_ssid_and_region(ssid_pattern, state_code):
    """Search for networks by SSID pattern and region - broad initial search"""
    params = {
        'ssidlike': ssid_pattern,
        'region': state_code,
        'onlymine': 'false',
        'freenet': 'false',
        'paynet': 'false'
    }
    
    response = make_wigle_request(API, params)
    if response and response.get('success'):
        return response.get('results', [])
    return []

def filter_by_bssid_prefixes(networks, bssid_prefixes):
    """Filter networks to only those with known BSSID prefixes"""
    filtered = []
    for network in networks:
        bssid = network.get('netid', '')
        if len(bssid) >= 8:  # Make sure BSSID is long enough
            bssid_prefix = bssid[:8]  # Get first 3 octets (XX:XX:XX format)
            if bssid_prefix in bssid_prefixes:
                filtered.append(network)
    return filtered

def filter_by_zip_codes(networks, zip_codes):
    """Filter networks to only those in specified ZIP codes"""
    filtered = []
    for network in networks:
        postal_code = network.get('postalcode', '')
        if postal_code in zip_codes:
            # Add ZIP code info to network
            network['zip_info'] = zip_codes[postal_code]
            filtered.append(network)
    return filtered

def add_wigle_urls(networks):
    """Add WiGLE map URLs to each network"""
    for network in networks:
        bssid = network.get('netid', '')
        if bssid:
            network['wigle_map_url'] = f"https://wigle.net/search?netid={bssid}"

def create_csv_export(networks, filename="output/surveillance_export.csv"):
    """
    Create a universal CSV file with WKT geometry format for mapping platforms
    Compatible with Google My Maps, ArcGIS, QGIS, and other GIS software
    
    Args:
        networks (list): List of network records to export
        filename (str): Output CSV filename
    """
    if not networks:
        print("No networks to export to CSV")
        return
    
    print(f"\nCreating universal CSV with WKT geometry format...")
    
    # Universal CSV headers for mapping platforms
    csv_headers = [
        'Name',           # Display name for the marker
        'Description',    # Details shown in popup
        'WKT',           # WKT geometry (POINT format) - Universal standard
        'SSID',          # Network SSID
        'BSSID',         # Network BSSID (MAC address)
        'City',          # City from our ZIP code dictionary
        'County',        # County from our ZIP code dictionary  
        'ZIP',           # ZIP code
        'Latitude',      # Decimal degrees latitude
        'Longitude',     # Decimal degrees longitude
        'First_Seen',    # First detection date
        'Last_Seen',     # Last detection date
        'Wigle_URL'      # Link to Wigle map
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
            writer.writeheader()
            
            for network in networks:
                # Extract data from network record
                ssid = network.get('ssid', 'Unknown')
                bssid = network.get('netid', 'Unknown')
                latitude = network.get('trilat', 0)
                longitude = network.get('trilong', 0)
                zip_info = network.get('zip_info', {})
                city = zip_info.get('city', 'Unknown')
                county = zip_info.get('county', 'Unknown')
                zip_code = network.get('postalcode', 'Unknown')
                first_seen = network.get('firsttime', 'Unknown')
                last_seen = network.get('lasttime', 'Unknown')
                wigle_url = network.get('wigle_map_url', '')
                
                # Create WKT POINT geometry - format: POINT(longitude latitude)
                wkt_point = f"POINT({longitude} {latitude})"
                
                # Create display name for the marker
                marker_name = f"ALPR Camera - {city}"
                
                # Create description with key details
                description = f"ALPR Surveillance Camera - SSID: {ssid} - BSSID: {bssid} - Location: {city}, {county} County - ZIP: {zip_code}"
                
                # Write CSV row
                writer.writerow({
                    'Name': marker_name,
                    'Description': description,
                    'WKT': wkt_point,
                    'SSID': ssid,
                    'BSSID': bssid,
                    'City': city,
                    'County': county,
                    'ZIP': zip_code,
                    'Latitude': latitude,
                    'Longitude': longitude,
                    'First_Seen': first_seen,
                    'Last_Seen': last_seen,
                    'Wigle_URL': wigle_url
                })
        
        print(f"Universal CSV created: {filename}")
        print(f"{len(networks)} camera locations exported")
        print(f"Compatible with Google My Maps, ArcGIS, QGIS, and other GIS platforms")
        
    except Exception as e:
        print(f"Error creating CSV file: {e}")

def create_kml_export(networks, filename="output/surveillance_locations.kml"):
    """
    Create a KML file for universal mapping platform compatibility
    Compatible with Google Earth, Google Maps, ArcGIS, QGIS, and other mapping software
    
    Args:
        networks (list): List of network records to export
        filename (str): Output KML filename
    """
    if not networks:
        print("No networks to export to KML")
        return
    
    print(f"\nCreating universal KML file...")
    
    try:
        with open(filename, 'w', encoding='utf-8') as kmlfile:
            # Write KML header
            kmlfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            kmlfile.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            kmlfile.write('  <Document>\n')
            kmlfile.write('    <n>ALPR Surveillance Camera Locations</n>\n')
            kmlfile.write('    <description>FlockFinder Project - Discovered surveillance camera locations</description>\n')
            
            # Define shared style for all placemarks
            kmlfile.write('    <Style id="surveillanceCamera">\n')
            kmlfile.write('      <IconStyle>\n')
            kmlfile.write('        <scale>1.2</scale>\n')
            kmlfile.write('        <Icon>\n')
            kmlfile.write('          <href>http://maps.google.com/mapfiles/kml/shapes/camera.png</href>\n')
            kmlfile.write('        </Icon>\n')
            kmlfile.write('        <color>ff0000ff</color>\n')  # Red color for visibility
            kmlfile.write('      </IconStyle>\n')
            kmlfile.write('      <LabelStyle>\n')
            kmlfile.write('        <scale>0.8</scale>\n')
            kmlfile.write('      </LabelStyle>\n')
            kmlfile.write('    </Style>\n')
            
            # Create a placemark for each network
            for network in networks:
                # Extract data from network record
                ssid = network.get('ssid', 'Unknown')
                bssid = network.get('netid', 'Unknown')
                latitude = network.get('trilat', 0)
                longitude = network.get('trilong', 0)
                zip_info = network.get('zip_info', {})
                city = zip_info.get('city', 'Unknown')
                county = zip_info.get('county', 'Unknown')
                zip_code = network.get('postalcode', 'Unknown')
                first_seen = network.get('firsttime', 'Unknown')
                last_seen = network.get('lasttime', 'Unknown')
                wigle_url = network.get('wigle_map_url', '')
                
                # Escape XML special characters in text content
                def escape_xml(text):
                    if not text or text == 'Unknown':
                        return text
                    return (str(text).replace('&', '&amp;')
                                   .replace('<', '&lt;')
                                   .replace('>', '&gt;')
                                   .replace('"', '&quot;')
                                   .replace("'", '&apos;'))
                
                # Create placemark name and description
                placemark_name = escape_xml(f"ALPR Camera - {city}")
                
                # Create detailed description with HTML formatting
                description_html = f"""<![CDATA[
<h3>ALPR Surveillance Camera</h3>
<table border="1" cellpadding="3">
<tr><td><b>SSID:</b></td><td>{escape_xml(ssid)}</td></tr>
<tr><td><b>BSSID:</b></td><td>{escape_xml(bssid)}</td></tr>
<tr><td><b>Location:</b></td><td>{escape_xml(city)}, {escape_xml(county)} County</td></tr>
<tr><td><b>ZIP Code:</b></td><td>{escape_xml(zip_code)}</td></tr>
<tr><td><b>Coordinates:</b></td><td>{latitude}, {longitude}</td></tr>
<tr><td><b>First Seen:</b></td><td>{escape_xml(first_seen)}</td></tr>
<tr><td><b>Last Seen:</b></td><td>{escape_xml(last_seen)}</td></tr>
<tr><td><b>Wigle Map:</b></td><td><a href="{wigle_url}">View on Wigle.net</a></td></tr>
</table>
<p><i>Discovered by FlockFinder Project</i></p>
]]>"""
                
                # Write placemark KML
                kmlfile.write('    <Placemark>\n')
                kmlfile.write(f'      <n>{placemark_name}</n>\n')
                kmlfile.write(f'      <description>{description_html}</description>\n')
                kmlfile.write('      <styleUrl>#surveillanceCamera</styleUrl>\n')
                kmlfile.write('      <Point>\n')
                kmlfile.write(f'        <coordinates>{longitude},{latitude},0</coordinates>\n')
                kmlfile.write('      </Point>\n')
                
                # Add extended data for compatibility with GIS software
                kmlfile.write('      <ExtendedData>\n')
                kmlfile.write(f'        <Data name="SSID"><value>{escape_xml(ssid)}</value></Data>\n')
                kmlfile.write(f'        <Data name="BSSID"><value>{escape_xml(bssid)}</value></Data>\n')
                kmlfile.write(f'        <Data name="City"><value>{escape_xml(city)}</value></Data>\n')
                kmlfile.write(f'        <Data name="County"><value>{escape_xml(county)}</value></Data>\n')
                kmlfile.write(f'        <Data name="ZIP"><value>{escape_xml(zip_code)}</value></Data>\n')
                kmlfile.write(f'        <Data name="Latitude"><value>{latitude}</value></Data>\n')
                kmlfile.write(f'        <Data name="Longitude"><value>{longitude}</value></Data>\n')
                kmlfile.write(f'        <Data name="First_Seen"><value>{escape_xml(first_seen)}</value></Data>\n')
                kmlfile.write(f'        <Data name="Last_Seen"><value>{escape_xml(last_seen)}</value></Data>\n')
                kmlfile.write(f'        <Data name="Wigle_URL"><value>{wigle_url}</value></Data>\n')
                kmlfile.write('      </ExtendedData>\n')
                
                kmlfile.write('    </Placemark>\n')
            
            # Close KML document
            kmlfile.write('  </Document>\n')
            kmlfile.write('</kml>\n')
        
        print(f"Universal KML created: {filename}")
        print(f"{len(networks)} camera locations exported")
        print(f"Compatible with Google Earth, Google Maps, ArcGIS, QGIS, and other mapping platforms")
        
    except Exception as e:
        print(f"Error creating KML file: {e}")

def display_final_summary(networks, search_info):
    """Display clean final summary"""
    print("\n" + "="*60)
    print("FLOCKFINDER RESULTS SUMMARY")
    print("="*60)
    
    if networks:
        print(f"{len(networks)} potential surveillance cameras detected")
        print(f"Search completed: {search_info.get('search_timestamp', 'N/A')}")
        
        # Get ZIP code count from search parameters
        search_params = search_info.get('search_parameters', {})
        zip_count = search_params.get('zip_codes_count', 0)
        print(f"Coverage: {zip_count} ZIP codes")
        
        # Group by county for summary
        county_counts = {}
        for network in networks:
            zip_info = network.get('zip_info', {})
            county = zip_info.get('county', 'Unknown')
            county_counts[county] = county_counts.get(county, 0) + 1
        
        print(f"\nDetection breakdown by county:")
        for county, count in sorted(county_counts.items()):
            print(f"   • {county}: {count} cameras")
            
        print(f"\nFiles generated:")
        print(f"   • output/surveillance_results.json - Complete data with metadata")
        print(f"   • output/surveillance_export.csv - Universal CSV for analysis")
        print(f"   • output/surveillance_locations.kml - Google Earth visualization")
        
    else:
        print("No surveillance cameras detected in selected area")
        print("   • Try expanding search area")
        print("   • Check if BSSID/SSID prefixes need updating")
    
    print("="*60)

### MAIN EXECUTION ###
def main():
    global BSSIDS, SSIDS, ZIPCODES
    
    print("FlockFinder - ALPR Surveillance Camera Detection")
    print("=" * 50)
    
    # Load BSSID prefixes from external JSON file
    BSSIDS = load_bssid_prefixes()
    
    if not BSSIDS:
        print("No BSSID prefixes loaded. Cannot proceed with search.")
        print("Please create or fix the known_bssid_prefixes.json file")
        return
    
    # Load SSID prefixes from external JSON file
    SSIDS = load_ssid_prefixes()
    
    if not SSIDS:
        print("No SSID prefixes loaded. Cannot proceed with search.")
        print("Please create or fix the known_ssid_prefixes.json file")
        return
    
    # Interactive geographic region selection
    ZIPCODES, state_code = select_geographic_regions()
    
    if not ZIPCODES:
        print("No ZIP codes loaded. Cannot proceed with search.")
        return
    
    if not state_code:
        print("No state code determined. Cannot proceed with search.")
        return
    
    print(f"\nSearching for surveillance devices...")
    print(f"Known BSSID prefixes loaded: {len(BSSIDS)}")
    print(f"Known SSID prefixes loaded: {len(SSIDS)}")
    print(f"Geographic coverage: {len(ZIPCODES)} ZIP codes")
    print(f"Using region filter: {state_code}")
    
    # Search phase - broad SSID search first, then filter locally
    print("Scanning WiGLE database...")
    all_networks = []
    
    # Search by each SSID prefix in the target state
    total_prefixes = len(SSIDS)
    for i, ssid_prefix in enumerate(SSIDS, 1):
        print(f"   Progress: {i}/{total_prefixes} SSID prefixes", end='\r')
        
        networks = search_by_ssid_and_region(ssid_prefix, state_code)
        all_networks.extend(networks)
        
        time.sleep(1)  # Rate limiting
    
    print(f"\nProcessing {len(all_networks)} total networks...")
    
    # Filter by known BSSID prefixes
    print("Filtering by known BSSID prefixes...")
    bssid_filtered = filter_by_bssid_prefixes(all_networks, BSSIDS)
    print(f"After BSSID filtering: {len(bssid_filtered)} networks")
    
    # Filter by geographic area and add city/county info
    print("Filtering by selected geographic area...")
    final_filtered = filter_by_zip_codes(bssid_filtered, ZIPCODES)
    print(f"After geographic filtering: {len(final_filtered)} networks")
    
    # Add WiGLE URLs
    add_wigle_urls(final_filtered)
    
    # Prepare output data
    search_info = {
        'search_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_found_in_search': len(all_networks),
        'after_bssid_filter': len(bssid_filtered),
        'after_geographic_filter': len(final_filtered),
        'search_parameters': {
            'bssid_prefixes_count': len(BSSIDS),
            'ssid_prefixes_count': len(SSIDS),
            'zip_codes_count': len(ZIPCODES),
            'state_region': state_code
        }
    }
    
    output_data = {
        'search_info': search_info,
        'networks': final_filtered
    }
    
    # Save JSON results
    with open('output/surveillance_results.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Create exports
    create_csv_export(final_filtered)
    create_kml_export(final_filtered)
    
    # Display final summary
    display_final_summary(final_filtered, search_info)

if __name__ == "__main__":
    main()