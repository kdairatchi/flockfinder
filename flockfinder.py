#!/usr/bin/env python3
"""
FlockFinder - Wigle Database Scanner for Flock Safety ALPR Cameras
================================================================
Simple script to search Wigle database for Flock devices and filter by DFW area
Outputs both JSON and Google My Maps compatible CSV with WKT geometry
"""

### IMPORTS ###
import csv
import getpass
import json
import os
import requests
import sys
import time
from pprint import pprint

### GLOBALS ###
## Wigle API Authentication
# Checks if running in a GitHub Action or Codespaces
if os.environ.get('GITHUB_ACTIONS') == "true" or os.environ.get('CODESPACES') == "true":
    TOKEN = os.environ.get('WIGLE_TOKEN')
# Asks user for a token if not running in automation environment
else:
    TOKEN = getpass.getpass('Enter Wigle API Token: ')

HEADER = {"Authorization": "Basic " + TOKEN}
BASEURL = 'https://api.wigle.net'
API = '/api/v2/network/search'

# Known Flock device BSSID prefixes (first 3 octets)
BSSIDS = ["00:F4:8D", "08:3A:88", "14:5A:FC", "3C:91:80", "62:DD:4C", "70:C9:4E", 
          "74:4C:A1", "80:30:49", "86:A2:F4", "92:B7:DD", "94:08:53", "9C:2F:9D", 
          "A2:A2:F4", "A6:A2:F4", "B8:27:EB", "C0:C9:E3", "D0:39:57", "D8:F3:BC", 
          "E0:0A:F6", "E4:AA:EA", "E4:C3:2A", "E6:F4:C6", "E8:D0:FC", "F4:6A:DD", 
          "F6:7F:D7", "F8:A2:D6"]

# DFW Metroplex ZIP codes with corresponding cities and counties
ZIPCODES = {
    # Original North Dallas ZIP codes
    "75007": {"city": "Carrollton", "county": "Dallas"},
    "75009": {"city": "Celina", "county": "Collin"},
    "75010": {"city": "Carrollton", "county": "Denton"},
    "75019": {"city": "Coppell", "county": "Dallas"},
    "75022": {"city": "Flower Mound", "county": "Denton"},
    "75024": {"city": "Plano", "county": "Collin"},
    "75028": {"city": "Flower Mound", "county": "Denton"},
    "75034": {"city": "Frisco", "county": "Collin"},
    "75056": {"city": "The Colony", "county": "Denton"},
    "75057": {"city": "Lewisville", "county": "Denton"},
    "75065": {"city": "Lake Dallas", "county": "Denton"},
    "75067": {"city": "Lewisville", "county": "Denton"},
    "75068": {"city": "Little Elm", "county": "Denton"},
    "75077": {"city": "Lewisville", "county": "Denton"},
    "75078": {"city": "Plano", "county": "Collin"},
    "75093": {"city": "Plano", "county": "Collin"},
    "75287": {"city": "Dallas", "county": "Dallas"},
    "76052": {"city": "Haslet", "county": "Tarrant"},
    "76078": {"city": "Prosper", "county": "Collin"},
    "76092": {"city": "Southlake", "county": "Tarrant"},
    "76177": {"city": "Fort Worth", "county": "Tarrant"},
    "76201": {"city": "Denton", "county": "Denton"},
    "76205": {"city": "Denton", "county": "Denton"},
    "76207": {"city": "Denton", "county": "Denton"},
    "76208": {"city": "Denton", "county": "Denton"},
    "76209": {"city": "Denton", "county": "Denton"},
    "76210": {"city": "Denton", "county": "Denton"},
    "76226": {"city": "Krum", "county": "Denton"},
    "76227": {"city": "Roanoke", "county": "Denton"},
    "76234": {"city": "Decatur", "county": "Wise"},
    "76247": {"city": "Justin", "county": "Denton"},
    "76249": {"city": "Keller", "county": "Tarrant"},
    "76258": {"city": "Trophy Club", "county": "Denton"},
    "76259": {"city": "Ponder", "county": "Denton"},
    "76262": {"city": "Westlake", "county": "Tarrant"},
    "76266": {"city": "Lewisville", "county": "Denton"},
    "76272": {"city": "Sanger", "county": "Denton"},
    
    # Additional Dallas County ZIP codes
    "75201": {"city": "Dallas", "county": "Dallas"},
    "75202": {"city": "Dallas", "county": "Dallas"},
    "75203": {"city": "Dallas", "county": "Dallas"},
    "75204": {"city": "Dallas", "county": "Dallas"},
    "75205": {"city": "Highland Park", "county": "Dallas"},
    "75206": {"city": "Dallas", "county": "Dallas"},
    "75207": {"city": "Dallas", "county": "Dallas"},
    "75208": {"city": "Dallas", "county": "Dallas"},
    "75209": {"city": "Dallas", "county": "Dallas"},
    "75210": {"city": "Dallas", "county": "Dallas"},
    "75211": {"city": "Dallas", "county": "Dallas"},
    "75212": {"city": "Dallas", "county": "Dallas"},
    "75214": {"city": "Dallas", "county": "Dallas"},
    "75215": {"city": "Dallas", "county": "Dallas"},
    "75216": {"city": "Dallas", "county": "Dallas"},
    "75217": {"city": "Dallas", "county": "Dallas"},
    "75218": {"city": "Dallas", "county": "Dallas"},
    "75219": {"city": "Dallas", "county": "Dallas"},
    "75220": {"city": "Dallas", "county": "Dallas"},
    "75221": {"city": "Dallas", "county": "Dallas"},
    "75222": {"city": "Dallas", "county": "Dallas"},
    "75223": {"city": "Dallas", "county": "Dallas"},
    "75224": {"city": "Dallas", "county": "Dallas"},
    "75225": {"city": "Dallas", "county": "Dallas"},
    "75226": {"city": "Dallas", "county": "Dallas"},
    "75227": {"city": "Dallas", "county": "Dallas"},
    "75228": {"city": "Dallas", "county": "Dallas"},
    "75229": {"city": "Dallas", "county": "Dallas"},
    "75230": {"city": "Dallas", "county": "Dallas"},
    "75231": {"city": "Dallas", "county": "Dallas"},
    "75232": {"city": "Dallas", "county": "Dallas"},
    "75233": {"city": "Dallas", "county": "Dallas"},
    "75234": {"city": "Dallas", "county": "Dallas"},
    "75235": {"city": "Dallas", "county": "Dallas"},
    "75236": {"city": "Dallas", "county": "Dallas"},
    "75237": {"city": "Dallas", "county": "Dallas"},
    "75238": {"city": "Dallas", "county": "Dallas"},
    "75240": {"city": "Dallas", "county": "Dallas"},
    "75241": {"city": "Dallas", "county": "Dallas"},
    "75243": {"city": "Dallas", "county": "Dallas"},
    "75244": {"city": "Dallas", "county": "Dallas"},
    "75246": {"city": "Dallas", "county": "Dallas"},
    "75247": {"city": "Dallas", "county": "Dallas"},
    "75248": {"city": "Dallas", "county": "Dallas"},
    "75249": {"city": "Dallas", "county": "Dallas"},
    "75250": {"city": "Dallas", "county": "Dallas"},
    "75251": {"city": "Dallas", "county": "Dallas"},
    "75252": {"city": "Dallas", "county": "Dallas"},
    
    # Collin County ZIP codes
    "75013": {"city": "Allen", "county": "Collin"},
    "75023": {"city": "Plano", "county": "Collin"},
    "75025": {"city": "Plano", "county": "Collin"},
    "75035": {"city": "Frisco", "county": "Collin"},
    "75069": {"city": "McKinney", "county": "Collin"},
    "75070": {"city": "McKinney", "county": "Collin"},
    "75071": {"city": "McKinney", "county": "Collin"},
    "75072": {"city": "McKinney", "county": "Collin"},
    "75074": {"city": "Plano", "county": "Collin"},
    "75075": {"city": "Plano", "county": "Collin"},
    "75080": {"city": "Richardson", "county": "Collin"},
    "75081": {"city": "Richardson", "county": "Collin"},
    "75082": {"city": "Richardson", "county": "Collin"},
    "75085": {"city": "Richardson", "county": "Dallas"},
    "75086": {"city": "Plano", "county": "Collin"},
    "75087": {"city": "Rockwall", "county": "Rockwall"},
    "75094": {"city": "Plano", "county": "Collin"},
    "75098": {"city": "Wylie", "county": "Collin"},
    "75166": {"city": "Rockwall", "county": "Rockwall"},
    "75169": {"city": "Royse City", "county": "Rockwall"},
    
    # Tarrant County ZIP codes (Fort Worth area)
    "76001": {"city": "Arlington", "county": "Tarrant"},
    "76002": {"city": "Arlington", "county": "Tarrant"},
    "76003": {"city": "Arlington", "county": "Tarrant"},
    "76004": {"city": "Arlington", "county": "Tarrant"},
    "76005": {"city": "Arlington", "county": "Tarrant"},
    "76006": {"city": "Arlington", "county": "Tarrant"},
    "76007": {"city": "Arlington", "county": "Tarrant"},
    "76008": {"city": "Arlington", "county": "Tarrant"},
    "76010": {"city": "Arlington", "county": "Tarrant"},
    "76011": {"city": "Arlington", "county": "Tarrant"},
    "76012": {"city": "Arlington", "county": "Tarrant"},
    "76013": {"city": "Arlington", "county": "Tarrant"},
    "76014": {"city": "Arlington", "county": "Tarrant"},
    "76015": {"city": "Arlington", "county": "Tarrant"},
    "76016": {"city": "Arlington", "county": "Tarrant"},
    "76017": {"city": "Arlington", "county": "Tarrant"},
    "76018": {"city": "Arlington", "county": "Tarrant"},
    "76019": {"city": "Arlington", "county": "Tarrant"},
    "76020": {"city": "Azle", "county": "Tarrant"},
    "76021": {"city": "Bedford", "county": "Tarrant"},
    "76022": {"city": "Bedford", "county": "Tarrant"},
    "76028": {"city": "Burleson", "county": "Tarrant"},
    "76034": {"city": "Crowley", "county": "Tarrant"},
    "76039": {"city": "Euless", "county": "Tarrant"},
    "76040": {"city": "Euless", "county": "Tarrant"},
    "76051": {"city": "Grapevine", "county": "Tarrant"},
    "76054": {"city": "Hurst", "county": "Tarrant"},
    "76101": {"city": "Fort Worth", "county": "Tarrant"},
    "76102": {"city": "Fort Worth", "county": "Tarrant"},
    "76103": {"city": "Fort Worth", "county": "Tarrant"},
    "76104": {"city": "Fort Worth", "county": "Tarrant"},
    "76105": {"city": "Fort Worth", "county": "Tarrant"},
    "76106": {"city": "Fort Worth", "county": "Tarrant"},
    "76107": {"city": "Fort Worth", "county": "Tarrant"},
    "76108": {"city": "Fort Worth", "county": "Tarrant"},
    "76109": {"city": "Fort Worth", "county": "Tarrant"},
    "76110": {"city": "Fort Worth", "county": "Tarrant"},
    "76111": {"city": "Fort Worth", "county": "Tarrant"},
    "76112": {"city": "Fort Worth", "county": "Tarrant"},
    "76114": {"city": "Fort Worth", "county": "Tarrant"},
    "76115": {"city": "Fort Worth", "county": "Tarrant"},
    "76116": {"city": "Fort Worth", "county": "Tarrant"},
    "76117": {"city": "Fort Worth", "county": "Tarrant"},
    "76118": {"city": "Fort Worth", "county": "Tarrant"},
    "76119": {"city": "Fort Worth", "county": "Tarrant"},
    "76120": {"city": "Fort Worth", "county": "Tarrant"},
    "76121": {"city": "Fort Worth", "county": "Tarrant"},
    "76122": {"city": "Fort Worth", "county": "Tarrant"},
    "76123": {"city": "Fort Worth", "county": "Tarrant"},
    "76124": {"city": "Fort Worth", "county": "Tarrant"},
    "76126": {"city": "Fort Worth", "county": "Tarrant"},
    "76127": {"city": "Fort Worth", "county": "Tarrant"},
    "76129": {"city": "Fort Worth", "county": "Tarrant"},
    "76131": {"city": "Fort Worth", "county": "Tarrant"},
    "76132": {"city": "Fort Worth", "county": "Tarrant"},
    "76133": {"city": "Fort Worth", "county": "Tarrant"},
    "76134": {"city": "Fort Worth", "county": "Tarrant"},
    "76135": {"city": "Fort Worth", "county": "Tarrant"},
    "76136": {"city": "Fort Worth", "county": "Tarrant"},
    "76137": {"city": "Fort Worth", "county": "Tarrant"},
    "76140": {"city": "Fort Worth", "county": "Tarrant"},
    "76148": {"city": "Fort Worth", "county": "Tarrant"},
    "76155": {"city": "Fort Worth", "county": "Tarrant"},
    "76179": {"city": "Fort Worth", "county": "Tarrant"},
    "76180": {"city": "North Richland Hills", "county": "Tarrant"},
    "76182": {"city": "North Richland Hills", "county": "Tarrant"},
    
    # Additional surrounding areas
    "75101": {"city": "Bardwell", "county": "Ellis"},
    "75104": {"city": "Cedar Hill", "county": "Dallas"},
    "75115": {"city": "DeSoto", "county": "Dallas"},
    "75116": {"city": "Duncanville", "county": "Dallas"},
    "75134": {"city": "Lancaster", "county": "Dallas"},
    "75149": {"city": "Mesquite", "county": "Dallas"},
    "75150": {"city": "Mesquite", "county": "Dallas"},
    "75154": {"city": "Red Oak", "county": "Ellis"},
    "75180": {"city": "Garland", "county": "Dallas"},
    "75181": {"city": "Garland", "county": "Dallas"},
    "75182": {"city": "Garland", "county": "Dallas"},
    "75183": {"city": "Garland", "county": "Dallas"},
    "75184": {"city": "Garland", "county": "Dallas"},
    "75185": {"city": "Garland", "county": "Dallas"},
}

### FUNCTIONS ###

def search_wigle(params):
    """Simple function to make Wigle API request"""
    url = BASEURL + API
    try:
        response = requests.get(url, headers=HEADER, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def create_google_maps_csv(networks, filename="flock_cameras_for_google_maps.csv"):
    """
    Create a CSV file with WKT geometry format for Google My Maps import
    
    Args:
        networks (list): List of network records to export
        filename (str): Output CSV filename
    """
    if not networks:
        print("No networks to export to CSV")
        return
    
    print(f"\nCreating Google Maps CSV with WKT geometry format...")
    
    # CSV headers for Google My Maps
    csv_headers = [
        'Name',           # Display name for the marker
        'Description',    # Details shown in popup
        'WKT',           # WKT geometry (POINT format) - REQUIRED for Google My Maps
        'SSID',          # Network SSID
        'BSSID',         # Network BSSID (MAC address)
        'City',          # City from our ZIP code dictionary
        'County',        # County from our ZIP code dictionary  
        'ZIP',           # ZIP code
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
                # Note: WKT uses longitude first, then latitude (opposite of lat,lon)
                wkt_point = f"POINT({longitude} {latitude})"
                
                # Create display name for the marker
                marker_name = f"Flock Camera - {city}"
                
                # Create description with key details
                description = f"""Flock Safety ALPR Camera
SSID: {ssid}
BSSID: {bssid}
Location: {city}, {county} County
ZIP: {zip_code}
Coordinates: {latitude}, {longitude}
First Seen: {first_seen}
Last Seen: {last_seen}"""
                
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
                    'First_Seen': first_seen,
                    'Last_Seen': last_seen,
                    'Wigle_URL': wigle_url
                })
        
        print(f"✓ Google Maps CSV created: {filename}")
        print(f"✓ {len(networks)} camera locations exported")
        print(f"✓ Ready for import to Google My Maps")
        print(f"\nTo import to Google My Maps:")
        print(f"1. Go to https://mymaps.google.com/")
        print(f"2. Create a new map or open existing map") 
        print(f"3. Click 'Add layer' -> 'Import'")
        print(f"4. Upload the CSV file: {filename}")
        print(f"5. Select 'WKT' column for positioning")
        print(f"6. Customize markers and styling as desired")
        
    except Exception as e:
        print(f"Error creating CSV file: {e}")

def main():
    print("FlockFinder - Wigle Database Scanner")
    print("===================================")
    print(f"Searching for Flock devices in Texas...")
    print(f"Known BSSID prefixes: {len(BSSIDS)}")
    print(f"DFW area ZIP codes: {len(ZIPCODES)}")
    
    # Broader search: Get all flock networks in TX, then filter locally
    params = {
        'ssidlike': 'flock-%',
        'region': 'TX'
    }
    
    print("\nStep 1: Broad flock SSID search in TX...")
    result = search_wigle(params)
    
    if not result or not result.get('success'):
        print("Search failed or no results")
        return
    
    all_networks = result.get('results', [])
    total_results = result.get('totalResults', 0)
    
    print(f"Found {len(all_networks)} networks in this batch")
    print(f"Total results available: {total_results}")
    
    # Step 2: Filter by known BSSIDs
    print("\nStep 2: Filtering by known BSSID prefixes...")
    bssid_filtered = []
    for network in all_networks:
        bssid = network.get('netid', '')
        if len(bssid) >= 8:  # Make sure BSSID is long enough
            bssid_prefix = bssid[:8]  # Get first 3 octets (XX:XX:XX format)
            if bssid_prefix in BSSIDS:
                bssid_filtered.append(network)
    
    print(f"After BSSID filtering: {len(bssid_filtered)} networks")
    
    # Step 3: Filter by DFW area ZIP codes and add city/county info
    print("\nStep 3: Filtering by DFW area ZIP codes...")
    final_filtered = []
    for network in bssid_filtered:
        postal_code = network.get('postalcode', '')
        if postal_code in ZIPCODES:
            # Add city and county information from our dictionary
            network['zip_info'] = ZIPCODES[postal_code]
            final_filtered.append(network)
    
    print(f"After ZIP code filtering: {len(final_filtered)} networks")
    
    # Step 4: Add Wigle map URLs to each network
    print("\nStep 4: Adding Wigle map URLs...")
    for network in final_filtered:
        bssid = network.get('netid', '')
        if bssid:
            # Build Wigle map URL for this specific BSSID
            wigle_url = f"https://wigle.net/search?netid={bssid}"
            network['wigle_map_url'] = wigle_url
    
    # Step 5: Display summary of filtered results
    print("\nFiltered Results Summary:")
    print("=" * 50)
    if final_filtered:
        for i, network in enumerate(final_filtered, 1):
            zip_info = network.get('zip_info', {})
            print(f"Network {i}:")
            print(f"  SSID: {network.get('ssid', 'N/A')}")
            print(f"  BSSID: {network.get('netid', 'N/A')}")
            print(f"  City: {zip_info.get('city', 'N/A')}")
            print(f"  County: {zip_info.get('county', 'N/A')}")
            print(f"  ZIP: {network.get('postalcode', 'N/A')}")
            print(f"  Coordinates: {network.get('trilat', 'N/A')}, {network.get('trilong', 'N/A')}")
            print(f"  First seen: {network.get('firsttime', 'N/A')}")
            print(f"  Last seen: {network.get('lasttime', 'N/A')}")
            print(f"  Map URL: {network.get('wigle_map_url', 'N/A')}")
            print("-" * 30)
    else:
        print("No networks found matching all filters")
    
    # Step 6: Save filtered results to JSON file
    output_data = {
        'search_info': {
            'search_params': params,
            'search_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_found_in_search': len(all_networks),
            'after_bssid_filter': len(bssid_filtered),
            'final_filtered_count': len(final_filtered),
            'coverage_area': f"{len(ZIPCODES)} ZIP codes across DFW metroplex"
        },
        'filter_criteria': {
            'known_bssid_prefixes': BSSIDS,
            'zip_codes_covered': list(ZIPCODES.keys())
        },
        'networks': final_filtered
    }
    
    # Save JSON results
    with open('flock_results_filtered.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n📄 Results saved to: flock_results_filtered.json")
    
    # Step 7: Create Google My Maps CSV with WKT geometry format
    create_google_maps_csv(final_filtered)
    
    # Final summary
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"Final count: {len(final_filtered)} Flock networks found in DFW Metroplex")
    print(f"Coverage area: {len(ZIPCODES)} ZIP codes across Dallas, Tarrant, Collin, Denton, and Rockwall counties")
    
    # Summary statistics by county
    county_stats = {}
    for network in final_filtered:
        county = network.get('zip_info', {}).get('county', 'Unknown')
        if county not in county_stats:
            county_stats[county] = 0
        county_stats[county] += 1
    
    if county_stats:
        print("\nResults by County:")
        for county, count in sorted(county_stats.items()):
            print(f"  {county} County: {count} networks")

if __name__ == "__main__":
    main()