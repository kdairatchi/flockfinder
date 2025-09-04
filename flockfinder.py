#!/usr/bin/env python3
"""
FlockFinder - Wigle Database Scanner for Flock Safety ALPR Cameras
================================================================
Simple script to search Wigle database for Flock devices and filter by DFW area
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

def create_csv_export(networks, filename="flock_maps_import.csv"):
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
                # Note: WKT uses longitude first, then latitude (opposite of lat,lon)
                wkt_point = f"POINT({longitude} {latitude})"
                
                # Create display name for the marker
                marker_name = f"Flock Camera - {city}"
                
                # Create description with key details
                description = f"Flock Safety ALPR Camera - SSID: {ssid} - BSSID: {bssid} - Location: {city}, {county} County - ZIP: {zip_code}"
                
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
        
        print(f"✓ Universal CSV created: {filename}")
        print(f"✓ {len(networks)} camera locations exported")
        print(f"✓ Compatible with Google My Maps, ArcGIS, QGIS, and other GIS platforms")
        
    except Exception as e:
        print(f"Error creating CSV file: {e}")

def create_kml_export(networks, filename="flock_maps_import.kml"):
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
            kmlfile.write('    <name>Flock Safety ALPR Camera Locations</name>\n')
            kmlfile.write('    <description>FlockFinder Project - Discovered Flock Safety camera locations in DFW Metroplex</description>\n')
            
            # Define shared style for all placemarks
            kmlfile.write('    <Style id="flockCameraIcon">\n')
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
                placemark_name = escape_xml(f"Flock Camera - {city}")
                
                # Create detailed description with HTML formatting
                description_html = f"""<![CDATA[
<h3>Flock Safety ALPR Camera</h3>
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
                kmlfile.write(f'      <name>{placemark_name}</name>\n')
                kmlfile.write(f'      <description>{description_html}</description>\n')
                kmlfile.write('      <styleUrl>#flockCameraIcon</styleUrl>\n')
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
        
        print(f"✓ Universal KML created: {filename}")
        print(f"✓ {len(networks)} camera locations exported")
        print(f"✓ Compatible with Google Earth, Google Maps, ArcGIS, QGIS, and other mapping platforms")
        
    except Exception as e:
        print(f"Error creating KML file: {e}")

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
    
    # Step 7: Create universal CSV and KML exports for mapping platforms
    create_csv_export(final_filtered)
    create_kml_export(final_filtered)
    
    # Final summary
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"Final count: {len(final_filtered)} Flock networks found in DFW Metroplex")
    print(f"Coverage area: {len(ZIPCODES)} ZIP codes across Dallas, Tarrant, Collin, Denton, and Rockwall counties")
    
    # Output files summary
    print(f"\n📁 OUTPUT FILES CREATED:")
    print(f"  • flock_results_filtered.json - Complete data with metadata")
    print(f"  • flock_maps_import.csv - Universal CSV with WKT geometry")
    print(f"  • flock_maps_import.kml - Universal KML for mapping platforms")
    print(f"\n🗺️  COMPATIBLE MAPPING PLATFORMS:")
    print(f"  • Google My Maps / Google Earth")
    print(f"  • ArcGIS / ArcGIS Online")
    print(f"  • QGIS (Free & Open Source)")
    print(f"  • MapBox / Leaflet")
    print(f"  • Any GIS software supporting WKT or KML formats")
    
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