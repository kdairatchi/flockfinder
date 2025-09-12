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

from .config import DEBUG_MODE


def debug_print(*args, **kwargs):
    """Print debug message only if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        print("[DEBUG OUTPUT]", *args, **kwargs)


def get_output_directory() -> str:
    """Get path to output directory"""
    package_dir = os.path.dirname(__file__)
    output_dir = os.path.join(package_dir, '..', '..', 'output')
    return os.path.normpath(output_dir)


def ensure_output_directory():
    """Ensure output directory exists"""
    output_dir = get_output_directory()
    os.makedirs(output_dir, exist_ok=True)
    debug_print(f"Output directory ensured: {output_dir}")


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
    debug_print(f"Saving {len(networks)} networks to JSON format")
    ensure_output_directory()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    country_code = area_info.get('country_code', 'unknown')
    filename = os.path.join(get_output_directory(), f"surveillance_results_{country_code}_{timestamp}.json")
    
    debug_print(f"JSON filename: {filename}")
    
    output_data = {
        'search_info': search_info,
        'area_info': area_info,
        'networks': networks
    }
    
    debug_print(f"JSON data structure: {len(output_data)} top-level keys")
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"JSON results saved: {filename}")
        debug_print(f"JSON file successfully written: {os.path.getsize(filename)} bytes")
        return filename
        
    except IOError as e:
        print(f"Error saving JSON file: {e}")
        debug_print(f"JSON write error: {e}")
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
        debug_print("CSV export skipped - no networks provided")
        return ""
    
    debug_print(f"Creating CSV export for {len(networks)} networks")
    ensure_output_directory()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    country_code = area_info.get('country_code', 'unknown')
    filename = os.path.join(get_output_directory(), f"surveillance_export_{country_code}_{timestamp}.csv")
    
    debug_print(f"CSV filename: {filename}")
    
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
    
    debug_print(f"CSV headers: {csv_headers}")
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
            writer.writeheader()
            debug_print("CSV headers written")
            
            for i, network in enumerate(networks, 1):
                # Extract data from network record
                ssid = network.get('ssid', 'Unknown')
                bssid = network.get('netid', 'Unknown')
                latitude = network.get('trilat') or network.get('latitude', 0)
                longitude = network.get('trilong') or network.get('longitude', 0)
                city = network.get('city', 'Unknown')
                first_seen = network.get('firsttime', 'Unknown')
                last_seen = network.get('lasttime', 'Unknown')
                wigle_url = network.get('wigle_map_url', '')
                
                debug_print(f"Processing network {i}: {bssid} in {city}")
                
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
        
        debug_print(f"CSV file successfully created: {os.path.getsize(filename)} bytes")
        return filename
        
    except IOError as e:
        print(f"Error creating CSV file: {e}")
        debug_print(f"CSV write error: {e}")
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
        debug_print("KML export skipped - no networks provided")
        return ""
    
    debug_print(f"Creating KML export for {len(networks)} networks")
    ensure_output_directory()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    country_code = area_info.get('country_code', 'unknown')
    filename = os.path.join(get_output_directory(), f"surveillance_locations_{country_code}_{timestamp}.kml")
    
    debug_print(f"KML filename: {filename}")
    
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
            kmlfile.write(f'    <name>ALPR Surveillance Cameras - {area_info.get("country", "Unknown")}</name>\n')
            kmlfile.write('    <description>FlockFinder Project - Discovered surveillance camera locations</description>\n')
            
            debug_print("KML header written")
            
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
            
            debug_print("KML style defined")
            
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
                
                debug_print(f"Creating KML placemark {i}: {bssid} in {city}")
                
                kmlfile.write(f'    <Placemark>\n')
                kmlfile.write(f'      <name>ALPR Camera {i} - {city}</name>\n')
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
            
            debug_print("KML placemarks written")
        
        print(f"KML file created: {filename}")
        print(f"{len(networks)} camera locations exported for Google Earth")
        
        debug_print(f"KML file successfully created: {os.path.getsize(filename)} bytes")
        return filename
        
    except IOError as e:
        print(f"Error creating KML file: {e}")
        debug_print(f"KML write error: {e}")
        return ""


def display_final_summary(networks: List[Dict], search_info: Dict, files_created: List[str]) -> None:
    """
    Display final summary of search results and created files
    
    Args:
        networks (list): List of detected surveillance cameras
        search_info (dict): Search metadata and parameters
        files_created (list): List of output files created
    """
    debug_print("Displaying final summary")
    
    print("\n" + "="*60)
    print("FLOCKFINDER SEARCH SUMMARY")
    print("="*60)
    
    # Search statistics
    print(f"Search completed: {search_info.get('search_timestamp', 'Unknown')}")
    print(f"Total networks found: {search_info.get('total_found_in_search', 0)}")
    print(f"After BSSID filtering: {search_info.get('after_bssid_filter', 0)}")
    print(f"Final surveillance cameras: {len(networks)}")
    
    debug_print(f"Summary stats - Total: {search_info.get('total_found_in_search', 0)}, Filtered: {search_info.get('after_bssid_filter', 0)}, Final: {len(networks)}")
    
    # Search parameters
    params = search_info.get('search_parameters', {})
    print(f"\nSearch Parameters:")
    print(f"  BSSID prefixes: {params.get('bssid_prefixes_count', 0)}")
    print(f"  SSID prefixes: {params.get('ssid_prefixes_count', 0)}")
    print(f"  Geographic area: {params.get('country', 'Unknown')}")
    if params.get('admin_selections'):
        print(f"  Administrative areas: {', '.join(params['admin_selections'])}")
    
    debug_print(f"Search parameters: {params}")
    
    # Files created
    if files_created:
        print(f"\nOutput Files Created:")
        for file_path in files_created:
            if file_path:
                file_basename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                print(f"  {file_basename} ({file_size:,} bytes)")
                debug_print(f"File created: {file_path} ({file_size} bytes)")
    
    # Camera locations summary
    if networks:
        cities = {}
        ssids = {}
        bssids = {}
        
        for network in networks:
            city = network.get('city', 'Unknown')
            cities[city] = cities.get(city, 0) + 1
            
            ssid = network.get('ssid', 'Unknown')
            ssids[ssid] = ssids.get(ssid, 0) + 1
            
            bssid = network.get('netid', '')
            if len(bssid) >= 8:
                bssid_prefix = bssid[:8]
                bssids[bssid_prefix] = bssids.get(bssid_prefix, 0) + 1
        
        debug_print(f"Analysis - Cities: {len(cities)}, SSIDs: {len(ssids)}, BSSID prefixes: {len(bssids)}")
        
        print(f"\nCamera Locations by City:")
        for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True):
            print(f"  {city}: {count} camera(s)")
        
        if len(ssids) > 1 and len(ssids) <= 10:  # Only show if reasonable number
            print(f"\nSSID Patterns Found:")
            for ssid, count in sorted(ssids.items(), key=lambda x: x[1], reverse=True)[:5]:  # Top 5 only
                print(f"  {ssid}: {count} network(s)")
        elif len(ssids) > 10:
            print(f"\nSSID Summary: {len(ssids)} unique patterns found (top 3 shown)")
            for ssid, count in sorted(ssids.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"  {ssid}: {count} network(s)")
            print(f"  ... and {len(ssids) - 3} more patterns")
        
        if DEBUG_MODE and len(bssids) > 1:
            debug_print("BSSID prefix breakdown:")
            for bssid_prefix, count in sorted(bssids.items(), key=lambda x: x[1], reverse=True):
                debug_print(f"  {bssid_prefix}: {count} network(s)")
    else:
        print("\nNo surveillance cameras found in the selected area.")
        print("Consider:")
        print("  - Expanding the search area")
        print("  - Checking BSSID and SSID prefix configurations")
        print("  - Verifying WiGLE API connectivity")
        
        debug_print("No cameras found - provided suggestions to user")
    
    print("\n" + "="*60)
    debug_print("Final summary display completed")


def create_summary_report(networks: List[Dict], search_info: Dict, area_info: Dict) -> Dict:
    """
    Create detailed summary report for analysis
    
    Args:
        networks (list): List of surveillance camera records
        search_info (dict): Search metadata and parameters
        area_info (dict): Geographic area information
        
    Returns:
        dict: Comprehensive summary report
    """
    debug_print(f"Creating summary report for {len(networks)} networks")
    
    # Basic statistics
    total_networks = len(networks)
    unique_cities = len(set(network.get('city', 'Unknown') for network in networks))
    unique_ssids = len(set(network.get('ssid', 'Unknown') for network in networks))
    unique_bssids = len(set(network.get('netid', 'Unknown') for network in networks))
    
    # Geographic distribution
    city_distribution = {}
    for network in networks:
        city = network.get('city', 'Unknown')
        city_distribution[city] = city_distribution.get(city, 0) + 1
    
    # Time analysis
    timestamps = []
    for network in networks:
        last_seen = network.get('lasttime')
        if last_seen:
            timestamps.append(last_seen)
    
    # BSSID prefix analysis
    prefix_distribution = {}
    for network in networks:
        bssid = network.get('netid', '')
        if len(bssid) >= 8:
            prefix = bssid[:8]
            prefix_distribution[prefix] = prefix_distribution.get(prefix, 0) + 1
    
    report = {
        'summary': {
            'total_cameras': total_networks,
            'unique_cities': unique_cities,
            'unique_ssids': unique_ssids,
            'unique_bssids': unique_bssids,
            'search_timestamp': search_info.get('search_timestamp'),
            'search_area': area_info.get('country'),
            'admin_areas': area_info.get('admin_selections', [])
        },
        'distribution': {
            'by_city': dict(sorted(city_distribution.items(), key=lambda x: x[1], reverse=True)),
            'by_bssid_prefix': dict(sorted(prefix_distribution.items(), key=lambda x: x[1], reverse=True))
        },
        'search_parameters': search_info.get('search_parameters', {}),
        'efficiency': {
            'networks_found': search_info.get('total_found_in_search', 0),
            'after_filtering': search_info.get('after_bssid_filter', 0),
            'filter_efficiency': (search_info.get('after_bssid_filter', 0) / max(search_info.get('total_found_in_search', 1), 1)) * 100
        }
    }
    
    debug_print(f"Summary report created with {len(report)} sections")
    return report


def export_summary_report(report: Dict, area_info: Dict) -> str:
    """
    Export summary report to JSON file
    
    Args:
        report (dict): Summary report data
        area_info (dict): Geographic area information
        
    Returns:
        str: Path to exported report file
    """
    debug_print("Exporting summary report to file")
    ensure_output_directory()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    country_code = area_info.get('country_code', 'unknown')
    filename = os.path.join(get_output_directory(), f"search_summary_{country_code}_{timestamp}.json")
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        debug_print(f"Summary report exported: {filename}")
        return filename
        
    except IOError as e:
        debug_print(f"Summary report export error: {e}")
        return ""