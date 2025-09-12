#!/usr/bin/env python3
"""
FlockFinder - Main Application
=============================
ALPR surveillance camera detection using WiGLE database and OSM boundaries
"""

import argparse
import os
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
from .config import load_bssid_prefixes, load_ssid_prefixes, DEBUG_MODE


def debug_print(*args, **kwargs):
    """Print debug message only if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        print("[DEBUG MAIN]", *args, **kwargs)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="FlockFinder - ALPR surveillance camera detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m flockfinder                    # Normal operation
  python -m flockfinder --debug            # Enable debug output
  FLOCKFINDER_DEBUG=1 python -m flockfinder  # Debug via environment variable
        """
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug output (overrides FLOCKFINDER_DEBUG environment variable)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='FlockFinder 2.0.0'
    )
    
    return parser.parse_args()


def display_country_menu(countries):
    """Display country selection menu"""
    print("\n" + "="*60)
    print("FlockFinder - ALPR Camera Detection System")
    print("="*60)
    print("\nAvailable Countries:")
    
    for i, (country_code, country_name) in enumerate(countries.items(), 1):
        print(f"  {i:2d}. {country_name} ({country_code})")
    
    return countries


def display_state_menu(admin_divisions, level_name):
    """Display state/province selection menu"""
    print(f"\nAvailable {level_name}:")
    
    # Sort states alphabetically for easier selection
    sorted_states = sorted(admin_divisions.items(), key=lambda x: x[1].get('name', ''))
    
    menu_options = {}
    for i, (state_code, state_data) in enumerate(sorted_states, 1):
        state_name = state_data.get('name', state_code)
        print(f"  {i:2d}. {state_name}")
        menu_options[i] = {'code': state_code, 'name': state_name, 'data': state_data}
    
    return menu_options


def display_metro_menu(state_code: str, state_name: str) -> dict:
    """Display metro area selection menu for a specific state"""
    # Define major metro areas by state
    METRO_AREAS = {
        'TX': {
            'DFW': {
                'name': 'Dallas-Fort Worth Metroplex',
                'counties': ['Collin', 'Dallas', 'Denton', 'Ellis', 'Rockwall', 'Tarrant', 'Wise'],
                'description': 'Dallas, Fort Worth, Plano, Irving, Arlington'
            },
            'Houston': {
                'name': 'Greater Houston Area', 
                'counties': ['Harris', 'Fort Bend', 'Montgomery', 'Galveston', 'Brazoria', 'Austin', 'Chambers', 'Liberty', 'Waller'],
                'description': 'Houston, Sugar Land, The Woodlands, Pearland'
            },
            'Austin': {
                'name': 'Austin-Round Rock Metro',
                'counties': ['Travis', 'Williamson', 'Hays', 'Caldwell', 'Bastrop'],
                'description': 'Austin, Round Rock, Cedar Park, Georgetown'
            },
            'San Antonio': {
                'name': 'San Antonio Metro',
                'counties': ['Bexar', 'Comal', 'Guadalupe', 'Wilson', 'Medina'],
                'description': 'San Antonio, New Braunfels, Schertz'
            }
        }
        # Add more states as needed
    }
    
    metros = METRO_AREAS.get(state_code, {})
    if not metros:
        debug_print(f"No metro areas defined for {state_code}")
        return {}
    
    print(f"\nMajor Metro Areas in {state_name}:")
    
    menu_options = {}
    for i, (metro_code, metro_data) in enumerate(metros.items(), 1):
        name = metro_data['name']
        description = metro_data['description']
        county_count = len(metro_data['counties'])
        print(f"  {i:2d}. {name}")
        print(f"      ({description}) - {county_count} counties")
        menu_options[i] = {
            'code': metro_code,
            'name': name,
            'data': metro_data
        }
    
    # Add options for entire state and individual counties
    next_option = len(metros) + 1
    print(f"\n  {next_option}. Entire State ({state_name})")
    menu_options[next_option] = {
        'code': 'ENTIRE_STATE',
        'name': f'Entire {state_name}',
        'data': {'counties': []}
    }
    
    next_option += 1
    print(f"  {next_option}. Individual Counties (county-level selection)")
    menu_options[next_option] = {
        'code': 'INDIVIDUAL_COUNTIES',
        'name': 'Individual Counties',
        'data': {'counties': []}
    }
    
    return menu_options


def display_county_menu(state_code: str, state_name: str, admin_divisions: dict) -> dict:
    """Display county selection menu for a specific state"""
    print(f"\nCounties in {state_name}:")
    print("(Select one or more by entering comma-separated numbers)")
    
    # Sort counties alphabetically for easier selection
    sorted_counties = sorted(admin_divisions.items(), key=lambda x: x[1].get('name', ''))
    
    menu_options = {}
    for i, (county_code, county_data) in enumerate(sorted_counties, 1):
        county_name = county_data.get('name', county_code)
        coord_count = len(county_data.get('coordinates', []))
        print(f"  {i:2d}. {county_name} County ({coord_count} boundary points)")
        menu_options[i] = {
            'code': county_code,
            'name': county_name,
            'data': county_data
        }
    
    # Add option to select all counties
    next_option = len(sorted_counties) + 1
    print(f"\n  {next_option}. All Counties")
    menu_options[next_option] = {
        'code': 'ALL_COUNTIES', 
        'name': 'All Counties',
        'data': {'counties': list(admin_divisions.keys())}
    }
    
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


def get_state_code_for_wigle(country_code: str, admin_code: str) -> str:
    """Convert OSM admin code to WiGLE state code format"""
    if country_code == 'US':
        # For US, use the admin code directly (TX, CA, etc.)
        return admin_code
    else:
        # For other countries, may need different mapping
        return admin_code


def select_geographic_boundaries():
    """
    Interactive geographic boundary selection using OSM data
    Returns tuple of (bounding_box, area_info, wigle_state_code)
    """
    debug_print("Starting geographic boundary selection")
    print("Loading country data from OpenStreetMap...")
    
    # Supported countries (expand as we test more)
    SUPPORTED_COUNTRIES = {'US': 'United States'}
    
    # Step 1: Country Selection
    try:
        all_countries = get_available_countries()
        if not all_countries:
            print("Error: Could not load country data")
            return None, None, None
        
        # Filter to only supported countries
        countries = {code: name for code, name in all_countries.items() 
                    if code in SUPPORTED_COUNTRIES}
        
        if not countries:
            print("Error: No supported countries available")
            return None, None, None
            
    except Exception as e:
        print(f"Error loading countries: {e}")
        debug_print(f"Country loading error details: {e}")
        return None, None, None
    
    country_menu = display_country_menu(countries)
    country_list = list(countries.items())
    
    print(f"\nCurrently supported: {len(countries)} country")
    print("Want support for your country?")
    print("   * Submit a GitHub issue: https://github.com/PoppaShell/flockfinder/issues")
    print("   * Contribute a pull request with OSM boundary research")
    print("   * More countries coming in future updates!")
    
    while True:
        try:
            choice_input = input(f"\nSelect country (1-{len(countries)}) or press Enter for US: ").strip()
            
            # Default to US if just Enter is pressed
            if not choice_input:
                selected_country_code, selected_country_name = 'US', 'United States'
                break
                
            choice = int(choice_input)
            if 1 <= choice <= len(countries):
                selected_country_code, selected_country_name = country_list[choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(countries)}")
        except ValueError:
            print("Invalid input. Please enter a number or press Enter for US")
    
    print(f"\nSelected country: {selected_country_name}")
    debug_print(f"Country selected: {selected_country_code}")
    
    # Step 2: Load States/Provinces
    print("Loading states/provinces...")
    try:
        admin_level_1 = get_admin_divisions(selected_country_code, admin_level=4)
        if not admin_level_1:
            print("No states/provinces found for this country")
            return None, None, None
    except Exception as e:
        print(f"Error loading states: {e}")
        debug_print(f"State loading error: {e}")
        return None, None, None
    
    level_name = "States" if selected_country_code == "US" else "Provinces"
    
    # Step 3: State Selection
    state_menu = display_state_menu(admin_level_1, level_name)
    state_selections = get_user_selection(state_menu, "state")
    selected_state = state_selections[0]  # Support single state for now
    selected_state_code = selected_state['code']
    selected_state_name = selected_state['name']
    
    print(f"\nSelected state: {selected_state_name}")
    debug_print(f"State selected: {selected_state_code}")
    
    # Step 4: Metro/County Selection
    metro_menu = display_metro_menu(selected_state_code, selected_state_name)
    selected_boundaries = []
    area_description = []
    
    if metro_menu:
        metro_selections = get_user_selection(metro_menu, "option")
        selected_option = metro_selections[0]
        
        debug_print(f"Selected geographic option: {selected_option['code']}")
        
        if selected_option['code'] == 'ENTIRE_STATE':
            # Use entire state boundaries
            selected_boundaries = admin_level_1[selected_state_code]['coordinates']
            area_description = [selected_state_name]
            
        elif selected_option['code'] == 'INDIVIDUAL_COUNTIES':
            # Let user select individual counties
            county_menu = display_county_menu(selected_state_code, selected_state_name, admin_level_1)
            county_selections = get_user_selection(county_menu, "counties")
            
            for selection in county_selections:
                if selection['code'] == 'ALL_COUNTIES':
                    # All counties in state
                    for county_code, county_data in admin_level_1.items():
                        selected_boundaries.extend(county_data.get('coordinates', []))
                    area_description = [f"All counties in {selected_state_name}"]
                    break
                else:
                    # Individual county
                    county_data = admin_level_1.get(selection['code'])
                    if county_data:
                        selected_boundaries.extend(county_data.get('coordinates', []))
                        area_description.append(selection['name'])
                    
        else:
            # Metro area selected
            metro_data = selected_option['data']
            metro_counties = metro_data.get('counties', [])
            area_description = [selected_option['name']]
            
            # Map metro county names to OSM admin codes
            for county_name in metro_counties:
                for admin_code, admin_data in admin_level_1.items():
                    osm_name = admin_data.get('name', '').replace(' County', '').replace(' Parish', '')
                    if (county_name.lower() in osm_name.lower() or 
                        osm_name.lower() in county_name.lower()):
                        selected_boundaries.extend(admin_data.get('coordinates', []))
                        debug_print(f"Mapped metro county {county_name} to OSM {osm_name}")
                        break
    
    else:
        # No metro areas defined, use entire state
        selected_boundaries = admin_level_1[selected_state_code]['coordinates']
        area_description = [selected_state_name]
    
    print(f"\nSelected area: {', '.join(area_description)}")
    debug_print(f"Total boundary coordinates: {len(selected_boundaries)}")
    
    # Step 5: Calculate Bounding Box
    print("Calculating geographic boundaries...")
    try:
        if not selected_boundaries:
            print("Error: No boundary coordinates found")
            return None, None, None
        
        bounding_box = calculate_bounding_box(selected_boundaries)
        if not bounding_box:
            print("Error: Could not calculate bounding box")
            return None, None, None
        
        debug_print(f"Calculated bounding box: {bounding_box}")
        
        # Cache the boundary data for future use
        cache_boundary_data(selected_country_code, admin_level_1)
        
        # Get WiGLE-compatible state code
        wigle_state_code = get_state_code_for_wigle(selected_country_code, selected_state_code)
        debug_print(f"WiGLE state code: {wigle_state_code}")
        
        area_info = {
            'country': selected_country_name,
            'country_code': selected_country_code,
            'state_code': selected_state_code,
            'wigle_state_code': wigle_state_code,
            'admin_selections': area_description,
            'bounding_box': bounding_box
        }
        
        print(f"\nGeographic area configured:")
        print(f"  Country: {selected_country_name}")
        print(f"  State: {selected_state_name}")
        print(f"  Areas: {', '.join(area_description)}")
        print(f"  Bounding box: {bounding_box['south']:.4f}, {bounding_box['west']:.4f} to {bounding_box['north']:.4f}, {bounding_box['east']:.4f}")
        
        debug_print("Geographic boundary selection completed successfully")
        return bounding_box, area_info, wigle_state_code
        
    except Exception as e:
        print(f"Error calculating boundaries: {e}")
        debug_print(f"Boundary calculation error: {e}")
        return None, None, None


def main():
    """Main execution function"""
    args = parse_arguments()
    
    # Override debug mode if command line flag is provided
    if args.debug:
        os.environ['FLOCKFINDER_DEBUG'] = '1'
        # Reload the debug mode setting
        global DEBUG_MODE
        from .config import DEBUG_MODE
        debug_print("Debug mode enabled via command line")
    
    print("FlockFinder - ALPR Surveillance Camera Detection")
    print("=" * 50)
    
    # Load configuration files
    print("Loading configuration...")
    bssid_prefixes = load_bssid_prefixes()
    ssid_prefixes = load_ssid_prefixes()
    
    if not bssid_prefixes or not ssid_prefixes:
        print("Error: Required configuration files missing or invalid")
        print("Run 'python -m flockfinder.config' to check configuration status")
        sys.exit(1)
    
    debug_print(f"Loaded {len(bssid_prefixes)} BSSID prefixes, {len(ssid_prefixes)} SSID prefixes")
    
    # Authenticate with WiGLE API
    print("Authenticating with WiGLE API...")
    if not authenticate_wigle():
        print("Error: WiGLE API authentication failed")
        sys.exit(1)
    
    debug_print("WiGLE API authentication successful")
    
    # Interactive geographic boundary selection
    boundary_result = select_geographic_boundaries()
    if not boundary_result or len(boundary_result) != 3 or not boundary_result[0]:
        print("Error: Geographic boundary selection failed")
        sys.exit(1)
    
    bounding_box, area_info, wigle_state_code = boundary_result
    debug_print("Boundary selection completed, starting search")
    
    # Search WiGLE database
    print(f"\nSearching for surveillance devices...")
    print(f"BSSID prefixes loaded: {len(bssid_prefixes)}")
    print(f"SSID prefixes loaded: {len(ssid_prefixes)}")
    print(f"Search area: {area_info['country']} - {', '.join(area_info['admin_selections'])}")
    if wigle_state_code:
        print(f"State filter: {wigle_state_code}")
    
    print("\nScanning WiGLE database...")
    all_networks = []
    
    # Search by each SSID prefix within the bounding box
    total_prefixes = len(ssid_prefixes)
    for i, ssid_prefix in enumerate(ssid_prefixes, 1):
        print(f"   Progress: {i}/{total_prefixes} SSID prefixes", end='\r')
        debug_print(f"Searching for SSID pattern: {ssid_prefix}")
        
        # Use both bounding box and state code for more precise results
        networks = search_by_coordinates(ssid_prefix, bounding_box, wigle_state_code)
        debug_print(f"Found {len(networks)} networks for pattern {ssid_prefix}")
        all_networks.extend(networks)
        
        time.sleep(1)  # Rate limiting
    
    print(f"\nProcessing {len(all_networks)} total networks...")
    debug_print(f"Total networks before filtering: {len(all_networks)}")
    
    # Filter by known BSSID prefixes
    print("Filtering by known BSSID prefixes...")
    filtered_networks = filter_by_bssid_prefixes(all_networks, bssid_prefixes)
    print(f"After BSSID filtering: {len(filtered_networks)} potential cameras")
    debug_print(f"Networks after BSSID filtering: {len(filtered_networks)}")
    
    # Prepare output data
    search_info = {
        'search_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_found_in_search': len(all_networks),
        'after_bssid_filter': len(filtered_networks),
        'search_parameters': {
            'bssid_prefixes_count': len(bssid_prefixes),
            'ssid_prefixes_count': len(ssid_prefixes),
            'country': area_info['country'],
            'state_code': area_info.get('state_code'),
            'wigle_state_code': wigle_state_code,
            'admin_selections': area_info['admin_selections'],
            'bounding_box': bounding_box
        }
    }
    
    debug_print(f"Search info summary: {search_info}")
    
    # Save results in multiple formats
    files_created = []
    if filtered_networks:
        print("\nSaving results...")
        
        # Save JSON results
        json_file = save_json_results(filtered_networks, search_info, area_info)
        if json_file:
            files_created.append(json_file)
        
        # Create CSV export
        csv_file = create_csv_export(filtered_networks, area_info)
        if csv_file:
            files_created.append(csv_file)
        
        # Create KML export
        kml_file = create_kml_export(filtered_networks, area_info)
        if kml_file:
            files_created.append(kml_file)
    
    # Display final summary
    display_final_summary(filtered_networks, search_info, files_created)
    
    debug_print("Main execution completed successfully")


if __name__ == "__main__":
    main()