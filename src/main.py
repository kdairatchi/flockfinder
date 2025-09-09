#!/usr/bin/env python3
"""
FlockFinder - Main Application
=============================
ALPR surveillance camera detection using WiGLE database and OSM boundaries
"""

import sys
import time
from datetime import datetime

from .osm_boundaries import (
    get_available_countries,
    get_admin_divisions,
    calculate_bounding_box,
    cache_boundary_data
)
from .wigle_api import (
    authenticate_wigle,
    search_by_coordinates,
    filter_by_bssid_prefixes
)
from .output_formats import (
    save_json_results,
    create_csv_export,
    create_kml_export,
    display_final_summary
)
from .config import load_bssid_prefixes, load_ssid_prefixes


def display_country_menu(countries):
    """Display country selection menu"""
    print("\n" + "="*60)
    print("FlockFinder - ALPR Camera Detection System")
    print("="*60)
    print("\nAvailable Countries:")
    
    for i, (country_code, country_name) in enumerate(countries.items(), 1):
        print(f"  {i:2d}. {country_name} ({country_code})")
    
    return countries


def display_admin_menu(admin_divisions, level_name):
    """Display administrative division selection menu"""
    print(f"\nAvailable {level_name}:")
    
    menu_options = {}
    for i, (code, data) in enumerate(admin_divisions.items(), 1):
        name = data.get('name', code)
        print(f"  {i:2d}. {name}")
        menu_options[i] = {'code': code, 'name': name, 'data': data}
    
    print(f"\n  {len(admin_divisions) + 1}. All {level_name.lower()}")
    menu_options[len(admin_divisions) + 1] = {'code': 'ALL', 'name': f'All {level_name}'}
    
    return menu_options


def get_user_selection(menu_options, selection_type):
    """Get user selection from menu options"""
    while True:
        try:
            choice_input = input(f"\nSelect {selection_type} (1-{len(menu_options)}) or 'q' to quit: ").strip()
            if choice_input.lower() == 'q':
                print("Exiting FlockFinder")
                sys.exit(0)
            
            # Handle multiple selections (comma-separated)
            if ',' in choice_input:
                choices = [int(x.strip()) for x in choice_input.split(',')]
                selected = []
                for choice in choices:
                    if choice in menu_options:
                        selected.append(menu_options[choice])
                    else:
                        raise ValueError(f"Invalid selection: {choice}")
                return selected
            else:
                choice = int(choice_input)
                if choice in menu_options:
                    return [menu_options[choice]]
                else:
                    print(f"Please enter a number between 1 and {len(menu_options)}")
        except ValueError as e:
            print(f"Invalid input: {e}. Please enter valid numbers or 'q' to quit")


def select_geographic_boundaries():
    """
    Interactive geographic boundary selection using OSM data
    Returns bounding box coordinates for WiGLE API
    """
    print("Loading country data from OpenStreetMap...")
    
    # Step 1: Country Selection
    try:
        countries = get_available_countries()
        if not countries:
            print("Error: Could not load country data")
            return None, None
    except Exception as e:
        print(f"Error loading countries: {e}")
        return None, None
    
    country_menu = display_country_menu(countries)
    country_list = list(countries.items())
    
    while True:
        try:
            choice = int(input(f"\nSelect country (1-{len(countries)}) or 'q' to quit: ").strip())
            if 1 <= choice <= len(countries):
                selected_country_code, selected_country_name = country_list[choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(countries)}")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit")
    
    print(f"\nSelected country: {selected_country_name}")
    
    # Step 2: Administrative Division Selection (States/Provinces)
    print("Loading administrative divisions...")
    try:
        admin_level_1 = get_admin_divisions(selected_country_code, admin_level=4)  # States/Provinces
        if not admin_level_1:
            print("No administrative divisions found for this country")
            return None, None
    except Exception as e:
        print(f"Error loading administrative divisions: {e}")
        return None, None
    
    level_name = "States" if selected_country_code == "US" else "Provinces"
    admin_menu = display_admin_menu(admin_level_1, level_name)
    admin_selections = get_user_selection(admin_menu, f"{level_name.lower()}")
    
    selected_admin_codes = []
    for selection in admin_selections:
        if selection['code'] == 'ALL':
            selected_admin_codes = list(admin_level_1.keys())
            break
        else:
            selected_admin_codes.append(selection['code'])
    
    print(f"\nSelected {level_name.lower()}: {', '.join([s['name'] for s in admin_selections])}")
    
    # Step 3: Calculate Bounding Box
    print("Calculating geographic boundaries...")
    try:
        all_boundaries = []
        for admin_code in selected_admin_codes:
            boundary_data = admin_level_1[admin_code]
            if 'coordinates' in boundary_data:
                all_boundaries.extend(boundary_data['coordinates'])
        
        if not all_boundaries:
            print("Error: No boundary coordinates found")
            return None, None
        
        bounding_box = calculate_bounding_box(all_boundaries)
        if not bounding_box:
            print("Error: Could not calculate bounding box")
            return None, None
        
        # Cache the boundary data for future use
        cache_boundary_data(selected_country_code, admin_level_1)
        
        area_info = {
            'country': selected_country_name,
            'country_code': selected_country_code,
            'admin_selections': [s['name'] for s in admin_selections],
            'bounding_box': bounding_box
        }
        
        print(f"\nGeographic area configured:")
        print(f"  Country: {selected_country_name}")
        print(f"  {level_name}: {', '.join(area_info['admin_selections'])}")
        print(f"  Bounding box: {bounding_box['south']:.4f}, {bounding_box['west']:.4f} to {bounding_box['north']:.4f}, {bounding_box['east']:.4f}")
        
        return bounding_box, area_info
        
    except Exception as e:
        print(f"Error calculating boundaries: {e}")
        return None, None


def main():
    """Main execution function"""
    print("FlockFinder - ALPR Surveillance Camera Detection")
    print("=" * 50)
    
    # Load configuration files
    print("Loading configuration...")
    bssid_prefixes = load_bssid_prefixes()
    ssid_prefixes = load_ssid_prefixes()
    
    if not bssid_prefixes or not ssid_prefixes:
        print("Error: Required configuration files missing or invalid")
        print("Run 'python -m src.config' to check configuration status")
        sys.exit(1)
    
    # Authenticate with WiGLE API
    print("Authenticating with WiGLE API...")
    if not authenticate_wigle():
        print("Error: WiGLE API authentication failed")
        sys.exit(1)
    
    # Interactive geographic boundary selection
    bounding_box, area_info = select_geographic_boundaries()
    if not bounding_box or not area_info:
        print("Error: Geographic boundary selection failed")
        sys.exit(1)
    
    # Search WiGLE database
    print(f"\nSearching for surveillance devices...")
    print(f"BSSID prefixes loaded: {len(bssid_prefixes)}")
    print(f"SSID prefixes loaded: {len(ssid_prefixes)}")
    print(f"Search area: {area_info['country']} - {', '.join(area_info['admin_selections'])}")
    
    print("\nScanning WiGLE database...")
    all_networks = []
    
    # Search by each SSID prefix within the bounding box
    total_prefixes = len(ssid_prefixes)
    for i, ssid_prefix in enumerate(ssid_prefixes, 1):
        print(f"   Progress: {i}/{total_prefixes} SSID prefixes", end='\r')
        
        networks = search_by_coordinates(ssid_prefix, bounding_box)
        all_networks.extend(networks)
        
        time.sleep(1)  # Rate limiting
    
    print(f"\nProcessing {len(all_networks)} total networks...")
    
    # Filter by known BSSID prefixes
    print("Filtering by known BSSID prefixes...")
    filtered_networks = filter_by_bssid_prefixes(all_networks, bssid_prefixes)
    print(f"After BSSID filtering: {len(filtered_networks)} potential cameras")
    
    # Prepare output data
    search_info = {
        'search_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_found_in_search': len(all_networks),
        'after_bssid_filter': len(filtered_networks),
        'search_parameters': {
            'bssid_prefixes_count': len(bssid_prefixes),
            'ssid_prefixes_count': len(ssid_prefixes),
            'country': area_info['country'],
            'admin_selections': area_info['admin_selections'],
            'bounding_box': bounding_box
        }
    }
    
    # Save results in multiple formats
    files_created = []
    if filtered_networks:
        print("\nSaving results...")
        
        # Save JSON results
        json_file = save_json_results(filtered_networks, search_info, area_info)
        files_created.append(json_file)
        
        # Create CSV export
        csv_file = create_csv_export(filtered_networks, area_info)
        files_created.append(csv_file)
        
        # Create KML export
        kml_file = create_kml_export(filtered_networks, area_info)
        files_created.append(kml_file)
    
    # Display final summary
    display_final_summary(filtered_networks, search_info, files_created)


if __name__ == "__main__":
    main()