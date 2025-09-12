"""
Configuration Management
========================
Functions for loading and validating configuration files with debug mode support
"""

import json
import os
from typing import Dict, List, Optional


# Debug mode configuration
DEBUG_MODE = os.environ.get('FLOCKFINDER_DEBUG', '').lower() in ('1', 'true', 'yes')


def debug_print(*args, **kwargs):
    """Print debug message only if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        print("[DEBUG CONFIG]", *args, **kwargs)


def get_config_path(filename: str) -> str:
    """
    Get path to configuration file
    
    Args:
        filename (str): Configuration filename
        
    Returns:
        str: Full path to configuration file
    """
    # Get the package directory
    package_dir = os.path.dirname(__file__)
    
    # Look for config files in multiple locations
    config_paths = [
        os.path.join(package_dir, '..', '..', 'config', filename),  # Repository root config/
        os.path.join('config', filename),                          # Current directory config/
        filename                                                   # Current directory
    ]
    
    for config_path in config_paths:
        normalized_path = os.path.normpath(config_path)
        debug_print(f"Checking config path: {normalized_path}")
        if os.path.exists(normalized_path):
            debug_print(f"Found config file: {normalized_path}")
            return normalized_path
    
    # Return the first path as default (repository root config)
    default_path = os.path.normpath(config_paths[0])
    debug_print(f"Using default config path: {default_path}")
    return default_path


def get_data_path() -> str:
    """
    Get path to data directory
    
    Returns:
        str: Full path to data directory
    """
    package_dir = os.path.dirname(__file__)
    data_path = os.path.join(package_dir, '..', '..', 'data')
    return os.path.normpath(data_path)


def load_bssid_prefixes(filename: str = "known_bssid_prefixes.json") -> List[str]:
    """
    Load known BSSID prefixes from configuration file
    
    Args:
        filename (str): Configuration filename
        
    Returns:
        list: List of BSSID prefixes or empty list if failed
    """
    config_path = get_config_path(filename)
    debug_print(f"Loading BSSID prefixes from: {config_path}")
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                bssid_list = data.get('bssid_prefixes', [])
                
                if not bssid_list:
                    print(f"Error: No BSSID prefixes found in {config_path}")
                    print("The bssid_prefixes array is empty. Please add surveillance device BSSID prefixes.")
                    return []
                
                print(f"Loaded {len(bssid_list)} BSSID prefixes from configuration")
                debug_print(f"BSSID prefixes: {bssid_list}")
                return bssid_list
        else:
            print(f"Error: Configuration file not found: {config_path}")
            print("Please create the configuration file with known surveillance device BSSID prefixes")
            print("Run 'python -m flockfinder.config' to check configuration status")
            return []
            
    except json.JSONDecodeError as e:
        print(f"Error parsing {config_path}: {e}")
        return []
    except Exception as e:
        print(f"Error loading {config_path}: {e}")
        return []


def load_ssid_prefixes(filename: str = "known_ssid_prefixes.json") -> List[str]:
    """
    Load known SSID prefixes from configuration file
    
    Args:
        filename (str): Configuration filename
        
    Returns:
        list: List of SSID prefixes or empty list if failed
    """
    config_path = get_config_path(filename)
    debug_print(f"Loading SSID prefixes from: {config_path}")
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ssid_list = data.get('ssid_prefixes', [])
                
                if not ssid_list:
                    print(f"Error: No SSID prefixes found in {config_path}")
                    print("The ssid_prefixes array is empty. Please add surveillance device SSID prefixes.")
                    return []
                
                print(f"Loaded {len(ssid_list)} SSID prefixes from configuration")
                debug_print(f"SSID prefixes: {ssid_list}")
                return ssid_list
        else:
            print(f"Error: Configuration file not found: {config_path}")
            print("Please create the configuration file with known surveillance device SSID prefixes")
            print("Run 'python -m flockfinder.config' to check configuration status")
            return []
            
    except json.JSONDecodeError as e:
        print(f"Error parsing {config_path}: {e}")
        return []
    except Exception as e:
        print(f"Error loading {config_path}: {e}")
        return []


def validate_bssid_prefix(bssid_prefix: str) -> bool:
    """
    Validate BSSID prefix format
    
    Args:
        bssid_prefix (str): BSSID prefix to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    # BSSID prefix should be in format XX:XX:XX
    if len(bssid_prefix) != 8:
        return False
    
    if bssid_prefix[2] != ':' or bssid_prefix[5] != ':':
        return False
    
    # Check hex characters
    hex_chars = bssid_prefix.replace(':', '')
    if len(hex_chars) != 6:
        return False
    
    try:
        int(hex_chars, 16)
        return True
    except ValueError:
        return False


def validate_ssid_prefix(ssid_prefix: str) -> bool:
    """
    Validate SSID prefix format
    
    Args:
        ssid_prefix (str): SSID prefix to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    # SSID should be non-empty and reasonable length
    if not ssid_prefix or len(ssid_prefix) > 32:
        return False
    
    # Check for valid characters (basic ASCII printable)
    if not all(32 <= ord(c) <= 126 for c in ssid_prefix):
        return False
    
    return True


def validate_configuration(bssid_prefixes: List[str], ssid_prefixes: List[str]) -> bool:
    """
    Validate loaded configuration data
    
    Args:
        bssid_prefixes (list): List of BSSID prefixes
        ssid_prefixes (list): List of SSID prefixes
        
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    if not bssid_prefixes:
        print("Error: No BSSID prefixes configured")
        return False
    
    if not ssid_prefixes:
        print("Error: No SSID prefixes configured")
        return False
    
    # Validate BSSID prefixes
    invalid_bssids = []
    for bssid in bssid_prefixes:
        if not validate_bssid_prefix(bssid):
            invalid_bssids.append(bssid)
    
    if invalid_bssids:
        print(f"Warning: Invalid BSSID prefixes found: {invalid_bssids}")
    
    # Validate SSID prefixes
    invalid_ssids = []
    for ssid in ssid_prefixes:
        if not validate_ssid_prefix(ssid):
            invalid_ssids.append(ssid)
    
    if invalid_ssids:
        print(f"Warning: Invalid SSID prefixes found: {invalid_ssids}")
    
    return True


def create_template_bssid_config(filename: str = "known_bssid_prefixes.json") -> str:
    """
    Create empty BSSID configuration template file
    
    Args:
        filename (str): Configuration filename
        
    Returns:
        str: Path to created configuration file
    """
    config_path = get_config_path(filename)
    
    template_config = {
        "description": "Known BSSID prefixes for surveillance and ALPR camera systems",
        "format": "First 3 octets of MAC address in XX:XX:XX format",
        "last_updated": "",
        "sources": [
            "Manual research - user must populate this list",
            "Community contributions",
            "Device documentation analysis"
        ],
        "bssid_prefixes": [
            # Users must populate this array with actual BSSID prefixes
            # Example format: "00:F4:8D", "08:3A:88", etc.
        ],
        "notes": [
            "This file is a template - the bssid_prefixes array is intentionally empty",
            "Users must research and add actual BSSID prefixes for surveillance devices",
            "Format: XX:XX:XX where X is a hexadecimal digit (0-9, A-F)",
            "Prefixes represent the first 3 octets (6 characters) of MAC addresses",
            "Update last_updated field when modifying the list"
        ]
    }
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(template_config, f, indent=2, ensure_ascii=False)
        
        print(f"Created BSSID configuration template: {config_path}")
        print("WARNING: Template file created with empty bssid_prefixes array")
        print("You must research and add actual BSSID prefixes before running FlockFinder")
        return config_path
        
    except IOError as e:
        print(f"Error creating BSSID configuration template: {e}")
        return ""


def create_template_ssid_config(filename: str = "known_ssid_prefixes.json") -> str:
    """
    Create empty SSID configuration template file
    
    Args:
        filename (str): Configuration filename
        
    Returns:
        str: Path to created configuration file
    """
    config_path = get_config_path(filename)
    
    template_config = {
        "description": "Known SSID patterns for surveillance and ALPR camera systems",
        "last_updated": "",
        "sources": [
            "Manual research - user must populate this list",
            "Field observations",
            "Device documentation analysis"
        ],
        "ssid_prefixes": [
            # Users must populate this array with actual SSID prefixes
            # Example format: "devicename-%", "prefix-%", etc.
        ],
        "notes": [
            "This file is a template - the ssid_prefixes array is intentionally empty",
            "Users must research and add actual SSID patterns for surveillance devices",
            "Use % symbol for wildcard matching in search patterns",
            "Patterns should identify WiFi networks broadcast by surveillance cameras",
            "Update last_updated field when modifying the list"
        ],
        "search_examples": [
            "pattern-% matches: pattern-ABC123, pattern-Camera01, etc.",
            "Use specific device naming patterns based on your research"
        ]
    }
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(template_config, f, indent=2, ensure_ascii=False)
        
        print(f"Created SSID configuration template: {config_path}")
        print("WARNING: Template file created with empty ssid_prefixes array")
        print("You must research and add actual SSID prefixes before running FlockFinder")
        return config_path
        
    except IOError as e:
        print(f"Error creating SSID configuration template: {e}")
        return ""


def check_dependencies() -> Dict[str, bool]:
    """
    Check for required dependencies and configuration files
    
    Returns:
        dict: Dependency check results
    """
    dependencies = {
        'bssid_config_exists': False,
        'bssid_config_populated': False,
        'ssid_config_exists': False,
        'ssid_config_populated': False,
        'output_directory': False,
        'cache_directory': False
    }
    
    # Check BSSID configuration
    bssid_path = get_config_path("known_bssid_prefixes.json")
    dependencies['bssid_config_exists'] = os.path.exists(bssid_path)
    debug_print(f"BSSID config exists: {dependencies['bssid_config_exists']} at {bssid_path}")
    
    if dependencies['bssid_config_exists']:
        bssid_prefixes = load_bssid_prefixes()
        dependencies['bssid_config_populated'] = len(bssid_prefixes) > 0
    
    # Check SSID configuration
    ssid_path = get_config_path("known_ssid_prefixes.json")
    dependencies['ssid_config_exists'] = os.path.exists(ssid_path)
    debug_print(f"SSID config exists: {dependencies['ssid_config_exists']} at {ssid_path}")
    
    if dependencies['ssid_config_exists']:
        ssid_prefixes = load_ssid_prefixes()
        dependencies['ssid_config_populated'] = len(ssid_prefixes) > 0
    
    # Check output directory
    package_dir = os.path.dirname(__file__)
    output_path = os.path.join(package_dir, '..', '..', 'output')
    normalized_output = os.path.normpath(output_path)
    dependencies['output_directory'] = os.path.exists(normalized_output)
    debug_print(f"Output directory exists: {dependencies['output_directory']} at {normalized_output}")
    
    # Check cache directory  
    cache_path = get_data_path()
    dependencies['cache_directory'] = os.path.exists(cache_path)
    debug_print(f"Cache directory exists: {dependencies['cache_directory']} at {cache_path}")
    
    return dependencies


def setup_project_structure() -> bool:
    """
    Set up required project directories and create template configuration files
    
    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        # Create required directories
        package_dir = os.path.dirname(__file__)
        directories = [
            get_data_path(),
            os.path.normpath(os.path.join(package_dir, '..', '..', 'output')),
            os.path.dirname(get_config_path('dummy'))  # Config directory
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
            debug_print(f"Directory created/verified: {directory}")
        
        # Create template configuration files if they don't exist
        bssid_path = get_config_path("known_bssid_prefixes.json")
        if not os.path.exists(bssid_path):
            create_template_bssid_config()
        
        ssid_path = get_config_path("known_ssid_prefixes.json")
        if not os.path.exists(ssid_path):
            create_template_ssid_config()
        
        print("\nProject structure setup complete")
        print("\nIMPORTANT: Configuration template files created with empty arrays")
        print("You must populate the following files with actual research data:")
        print(f"  - {bssid_path}")
        print(f"  - {ssid_path}")
        print("\nFlockFinder will not work until these files contain surveillance device signatures")
        
        return True
        
    except Exception as e:
        print(f"Error setting up project structure: {e}")
        debug_print(f"Setup error details: {e}", exc_info=True)
        return False


def get_configuration_summary() -> Dict:
    """
    Get summary of current configuration
    
    Returns:
        dict: Configuration summary
    """
    bssid_prefixes = load_bssid_prefixes()
    ssid_prefixes = load_ssid_prefixes()
    dependencies = check_dependencies()
    
    summary = {
        'bssid_count': len(bssid_prefixes),
        'ssid_count': len(ssid_prefixes),
        'dependencies': dependencies,
        'configuration_valid': validate_configuration(bssid_prefixes, ssid_prefixes),
        'ready_to_run': (len(bssid_prefixes) > 0 and 
                        len(ssid_prefixes) > 0 and 
                        dependencies['output_directory'] and 
                        dependencies['cache_directory']),
        'debug_mode': DEBUG_MODE
    }
    
    debug_print(f"Configuration summary: {summary}")
    return summary


def print_configuration_status() -> None:
    """Print current configuration status"""
    summary = get_configuration_summary()
    deps = summary['dependencies']
    
    print("\nFlockFinder Configuration Status:")
    print("=" * 40)
    print(f"Debug mode: {'On' if summary['debug_mode'] else 'Off'} (FLOCKFINDER_DEBUG={os.environ.get('FLOCKFINDER_DEBUG', 'not set')})")
    print(f"BSSID config file exists: {'Yes' if deps['bssid_config_exists'] else 'No'}")
    print(f"BSSID config populated: {'Yes' if deps['bssid_config_populated'] else 'No'} ({summary['bssid_count']} prefixes)")
    print(f"SSID config file exists: {'Yes' if deps['ssid_config_exists'] else 'No'}")
    print(f"SSID config populated: {'Yes' if deps['ssid_config_populated'] else 'No'} ({summary['ssid_count']} prefixes)")
    print(f"Output directory ready: {'Yes' if deps['output_directory'] else 'No'}")
    print(f"Cache directory ready: {'Yes' if deps['cache_directory'] else 'No'}")
    print(f"Ready to run: {'Yes' if summary['ready_to_run'] else 'No'}")
    
    if not summary['ready_to_run']:
        print("\nTo get started:")
        if not deps['bssid_config_exists'] or not deps['ssid_config_exists']:
            print("1. Run setup_project_structure() to create template files")
        if not deps['bssid_config_populated']:
            print("2. Add BSSID prefixes to known_bssid_prefixes.json")
        if not deps['ssid_config_populated']:
            print("3. Add SSID prefixes to known_ssid_prefixes.json")


def main():
    """Configuration management entry point"""
    print_configuration_status()
    
    summary = get_configuration_summary()
    if not summary['ready_to_run']:
        choice = input("\nWould you like to set up the project structure? (y/n): ").strip().lower()
        if choice == 'y':
            setup_project_structure()


if __name__ == "__main__":
    main()