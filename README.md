# FlockFinder

> Comprehensive ALPR surveillance camera detection and mapping using multiple automated discovery methods

## Overview

FlockFinder systematically locates and maps stationary ALPR (Automated License Plate Recognition) surveillance cameras using multiple automated discovery methods. The project targets all manufacturers and uses scalable techniques to provide comprehensive surveillance infrastructure mapping across communities.

## Features

### Current Implementation
- **Geographic Coverage**: Texas DFW and Houston metro areas with 315+ ZIP codes across 16 counties
- **WiFi Detection**: WiGLE database integration for surveillance devices broadcasting WiFi signals
- **Multi-Vendor Support**: Configurable BSSID prefix detection for various ALPR manufacturers
- **Interactive Selection**: Menu-driven geographic area selection with state, county, and multi-county options
- **Multiple Output Formats**: JSON, CSV, and KML for analysis and mapping platforms

### Detection Methods
**Currently Implemented:**
- **WiFi Intelligence**: Device discovery through WiGLE database integration and BSSID prefix matching

**Planned Development:**
- **Bluetooth Discovery**: BLE device detection through WiGLE database integration
- **Public Records Automation**: FOIA request processing and government contract analysis
- **Visual Recognition**: Satellite and street view imagery analysis using computer vision

### Multi-Vendor Detection
- **All ALPR Manufacturers**: Flock Safety, Motorola Solutions, Avigilon, OpenALPR, Rekor, and other vendors
- **Stationary Installations**: Fixed pole-mounted, traffic light mounted, and other permanent surveillance cameras

### Geographic Coverage
- **Current Support**: Texas DFW and Houston metropolitan areas
- **Expansion**: Additional states and counties are being developed
- **Community Requests**: Submit GitHub Issues to request coverage for specific areas
- **Contributions**: Pull Requests welcome for new geographic regions

### External Data Integration
- **WiGLE.net**: Community WiFi and Bluetooth database for device discovery
- **OpenStreetMap**: Geographic data and community mapping platform
- **DeFlock.me**: Community ALPR mapping project integration
- **EFF Atlas of Surveillance**: Cross-reference with known surveillance deployments
- **Public Records Databases**: Municipal contracts, budgets, and procurement records

## Installation

### Prerequisites
- Python 3.7 or higher
- WiGLE.net API account and token
- Required data files: `known_bssid_prefixes.json` and `geographic_registry.json`

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/PoppaShell/flockfinder.git
   cd flockfinder
   ```

2. Obtain WiGLE API credentials:
   - Visit https://wigle.net/ and create a free account
   - Navigate to your account settings and generate an API token

3. Ensure required data files are present in the repository

## Usage

### Basic Operation
```bash
python3 flockfinder.py
```

### Interactive Process
1. **WiGLE API Token** (if not set in environment variables)
2. **State Selection** from available states
3. **County Selection** (single, multiple, or all counties)
4. **Automated Processing** with progress indicator

### Environment Variables
```bash
export WIGLE_TOKEN="your_wigle_api_token_here"
```

## File Structure

```
flockfinder/
├── flockfinder.py                    # Main detection script
├── geographic_registry.json          # State and county definitions
├── known_bssid_prefixes.json         # Surveillance device BSSID prefixes
├── geographic_data/                  # County ZIP code databases
│   └── [state]_[county]_zips.json   # Individual county files
└── output/                           # Generated results
    ├── surveillance_results.json     # Complete search data
    ├── surveillance_export.csv       # Universal analysis format
    └── surveillance_locations.kml    # Google Earth visualization
```

## Privacy and Ethics

### Responsible Use
- **Privacy Research**: Understanding surveillance infrastructure deployment
- **Community Awareness**: Informing citizens about local monitoring systems
- **Academic Study**: Supporting research into surveillance networks
- **Transparency Advocacy**: Promoting informed policy discussions

### Data Sources
All detection uses publicly available information:
- **WiGLE Database**: Community-contributed WiFi and Bluetooth observations
- **Public Records**: Government transparency documents and contracts
- **Open Source Imagery**: Publicly accessible satellite and street view data

## Contributing

### Geographic Expansion
1. Create county ZIP code JSON files in `geographic_data/`
2. Update `geographic_registry.json` with new regions
3. Submit pull request with documentation

### Detection Method Development
- **Bluetooth Module**: BLE scanning integration with WiGLE data
- **Public Records Automation**: FOIA processing and contract analysis tools
- **Visual Recognition**: Computer vision pipelines for imagery analysis

### Community Support
- **GitHub Issues**: Request new geographic coverage areas
- **Pull Requests**: Contribute new regions or detection methods
- **Documentation**: Improve guides and technical documentation

## Legal Notice

This project operates within legal boundaries using only publicly available information. Users are responsible for ensuring compliance with local laws and regulations.

## Support

- **Issues**: GitHub issue tracker for bugs and feature requests
- **Coverage Requests**: Submit issues for new geographic areas
- **Community**: Contribute to open source surveillance transparency research

## License

Open source project supporting transparency and privacy research.