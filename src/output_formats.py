"""
Output Format Generation
========================
Functions for saving search results in multiple formats (JSON, CSV, KML)
and displaying summary information
"""

import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Optional


def get_output_directory() -> str:
    """Get path to output directory"""
    package_dir = os.path.dirname(__file__)
    output_dir = os.path.join(package_dir, '..', 'output')
    return os.path.normpath(output_dir)


def ensure_output_directory():
    """Ensure output directory exists"""
    output_dir = get_output_directory()
    os.makedirs(output_dir, exist_ok=True)


def save_json_results(networks: List[Dict], search_info: Dict, area_info: Dict) -> str:
    """
    Save search results in JSON format with metadata
    
    Args:
        networks (list): List of detected surveillance cameras
        search_info (dict): Search metadata and parameters
        area_info (dict): Geographic area information
        
    Returns:
        str: Path to saved JSON file
    """
    ensure_output_directory()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    country_code = area_info.get('country_code', 'unknown')
    filename = os.path.join(get_output_directory(), f"surveillance_results_{country_code}_{timestamp}.json")
    
    output_data = {
        'search_info': search_info,
        'area_info': area_info,
        'networks': networks
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"JSON results saved: {filename}")
        return filename
        
    except IOError as e:
        print(f"Error saving JSON file: {e}")
        return ""


def create_csv_export(networks: List[Dict], area_info: Dict) -> str:
    """
    Create universal CSV export with WKT geometry for mapping platforms
    
    Args:
        networks (list): List of surveillance camera records
        area_info (dict): Geographic area information
        
    Returns:
        str: Path to saved CSV file
    """
    if not networks:
        print("No networks to export to CSV")
        return ""
    
    ensure_output_directory()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    country_code = area_info.get('country_code', 'unknown')
    filename = os.path.join(get_output_directory(), f"surveillance_export_{country_code}_{timestamp}.csv")
    
    # Universal CSV headers for mapping platforms
    csv_headers = [
        'Name',
        'Description',
        'WKT',
        'SSID',
        'BSSID',
        'Country',
        'Admin_Area',
        'City',
        'Latitude',
        'Longitude',
        'First_Seen',
        'Last_Seen',
        'WiGLE_URL',
        'Discovery_Source'
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
            writer.writeheader()
            
            for network in networks:
                # Extract data from network record
                ssid = network.get('ssid', 'Unknown')
                bssid = network.get('netid', 'Unknown')
                latitude = network.get('trilat') or network.get('latitude', 0)
                longitude = network.get('trilong') or network.get('longitude', 0)
                city = network.get('city', 'Unknown')
                first_seen = network.get('firsttime', 'Unknown')
                last_seen = network.get('lasttime', 'Unknown')
                wigle_url = network.get('wigle_map_url', '')
                
                # Create WKT POINT geometry
                wkt_point = f"POINT({longitude} {latitude})"
                
                # Create display name and description
                marker_name = f"ALPR Camera - {city}"
                description = f"ALPR Surveillance Camera - SSID: {ssid} - BSSID: {bssid} - Location: {city}"
                
                # Write CSV row
                writer.writerow({
                    'Name': marker_name,
                    'Description': description,
                    'WKT': wkt_point,
                    'SSID': ssid,
                    'BSSID': bssid,
                    'Country': area_info.get('country', 'Unknown'),
                    'Admin_Area': ', '.join(area_info.get('admin_selections', [])),
                    'City': city,
                    'Latitude': latitude,
                    'Longitude': longitude,
                    'First_Seen': first_seen,
                    'Last_Seen': last_seen,
                    'WiGLE_URL': wigle_url,
                    'Discovery_Source': network.get('discovery_source', 'WiGLE.net')
                })
        
        print(f"Universal CSV created: {filename}")
        print(f"{len(networks)} camera locations exported")
        print(f"Compatible with Google My Maps, ArcGIS, QGIS, and other GIS platforms")
        
        return filename
        
    except IOError as e:
        print(f"Error creating CSV file: {e}")
        return ""


def create_kml_export(networks: List[Dict], area_info: Dict) -> str:
    """
    Create KML file for mapping visualization
    
    Args:
        networks (list): List of surveillance camera records
        area_info (dict): Geographic area information
        
    Returns:
        str: Path to saved KML file
    """
    if not networks:
        print("No networks to export to KML")
        return ""
    
    ensure_output_directory()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    country_code = area_info.get('country_code', 'unknown')
    filename = os.path.join(get_output_directory(), f"surveillance_locations_{country_code}_{timestamp}.kml")
    
    def escape_xml(text):
        """Escape XML special characters"""
        if not text or text == 'Unknown':
            return text
        return (str(text).replace('&', '&amp;')
                         .replace('<', '&lt;')
                         .replace('>', '&gt;')
                         .replace('"', '&quot;')
                         .replace("'", '&apos;'))
    
    try:
        with open(filename, 'w', encoding='utf-8') as kmlfile:
            # Write KML header
            kmlfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            kmlfile.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            kmlfile.write('  <Document>\n')
            kmlfile.write(f'    <n>ALPR Surveillance Cameras - {area_info.get("country", "Unknown")}</n>\n')
            kmlfile.write('    <description>FlockFinder Project - Discovered surveillance camera locations</description>\n')
            
            # Define shared style
            kmlfile.write('    <Style id="surveillanceCamera">\n')
            kmlfile.write('      <IconStyle>\n')
            kmlfile.write('        <scale>1.2</scale>\n')
            kmlfile.write('        <Icon>\n')
            kmlfile.write('          <href>http://maps.google.com/mapfiles/kml/shapes/camera.png</href>\n')
            kmlfile.write('        </Icon>\n')
            kmlfile.write('        <color>ff0000ff</color>\n')
            kmlfile.write('      </IconStyle>\n')
            kmlfile.write('      <LabelStyle>\n')
            kmlfile.write('        <scale>0.8</scale>\n')
            kmlfile.write('      </LabelStyle>\n')
            kmlfile.write('    </Style>\n')
            
            # Create placemarks for each network
            for i, network in enumerate(networks, 1):
                ssid = escape_xml(network.get('ssid', 'Unknown'))
                bssid = escape_xml(network.get('netid', 'Unknown'))
                latitude = network.get('trilat') or network.get('latitude', 0)
                longitude = network.get('trilong') or network.get('longitude', 0)
                city = escape_xml(network.get('city', 'Unknown'))
                first_seen = escape_xml(network.get('firsttime', 'Unknown'))
                last_seen = escape_xml(network.get('lasttime', 'Unknown'))
                wigle_url = escape_xml(network.get('wigle_map_url', ''))
                
                kmlfile.write(f'    <Placemark>\n')
                kmlfile.write(f'      <n>ALPR Camera {i} - {city}</n>\n')
                kmlfile.write(f'      <description><![CDATA[\n')
                kmlfile.write(f'        <b>ALPR Surveillance Camera</b><br/>\n')
                kmlfile.write(f'        <b>SSID:</b> {ssid}<br/>\n')
                kmlfile.write(f'        <b>BSSID:</b> {bssid}<br/>\n')
                kmlfile.write(f'        <b>Location:</b> {city}<br/>\n')
                kmlfile.write(f'        <b>First Seen:</b> {first_seen}<br/>\n')
                kmlfile.write(f'        <b>Last Seen:</b> {last_seen}<br/>\n')
                if wigle_url:
                    kmlfile.write(f'        <b>WiGLE URL:</b> <a href="{wigle_url}">View on WiGLE</a><br/>\n')
                kmlfile.write(f'        <b>Discovery Source:</b> {network.get("discovery_source", "WiGLE.net")}<br/>\n')
                kmlfile.write(f'      ]]></description>\n')
                kmlfile.write(f'      <styleUrl>#surveillanceCamera</styleUrl>\n')
                kmlfile.write(f'      <Point>\n')
                kmlfile.write(f'        <coordinates>{longitude},{latitude},0</coordinates>\n')
                kmlfile.write(f'      </Point>\n')
                kmlfile.write(f'    </Placemark>\n')
            
            # Close KML document
            kmlfile.write('  </Document>\n')
            kmlfile.write('</kml>\n')
        
        print(f"KML file created: {filename}")
        print(f"{len(networks)} camera locations exported for Google Earth")
        
        return filename
        
    except IOError as e:
        print(f"Error creating KML file: {e}")
        return ""


def display_final_summary(networks: List[Dict], search_info: Dict, files_created: List[str]) -> None:
    """
    Display final summary of search results and created files
    
    Args:
        networks (list): List of detected surveillance cameras
        search_info (dict): Search metadata and parameters
        files_created (list): List of output files created
    """
    print("\n" + "="*60)
    print("FLOCKFINDER SEARCH SUMMARY")
    print("="*60)
    
    # Search statistics
    print(f"Search completed: {search_info.get('search_timestamp', 'Unknown')}")
    print(f"Total networks found: {search_info.get('total_found_in_search', 0)}")
    print(f"After BSSID filtering: {search_info.get('after_bssid_filter', 0)}")
    print(f"Final surveillance cameras: {len(networks)}")
    
    # Search parameters
    params = search_info.get('search_parameters', {})
    print(f"\nSearch Parameters:")
    print(f"  BSSID prefixes: {params.get('bssid_prefixes_count', 0)}")
    print(f"  SSID prefixes: {params.get('ssid_prefixes_count', 0)}")
    print(f"  Geographic area: {params.get('country', 'Unknown')}")
    if params.get('admin_selections'):
        print(f"  Administrative areas: {', '.join(params['admin_selections'])}")
    
    # Files created
    if files_created:
        print(f"\nOutput Files Created:")
        for file_path in files_created:
            if file_path:
                print(f"  {os.path.basename(file_path)}")
    
    # Camera locations summary
    if networks:
        cities = {}
        for network in networks:
            city = network.get('city', 'Unknown')
            cities[city] = cities.get(city, 0) + 1
        
        print(f"\nCamera Locations by City:")
        for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True):
            print(f"  {city}: {count} camera(s)")
    else:
        print("\nNo surveillance cameras found in the selected area.")
        print("Consider:")
        print("  - Expanding the search area")
        print("  - Checking BSSID and SSID prefix configurations")
        print("  - Verifying WiGLE API connectivity")
    
    print("\n" + "="*60)