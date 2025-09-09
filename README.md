# FlockFinder

> Comprehensive ALPR surveillance camera detection and mapping using multiple automated discovery methods

## Overview

FlockFinder systematically locates and maps stationary ALPR (Automated License Plate Recognition) surveillance cameras using multiple automated discovery methods. The project targets all manufacturers and uses scalable techniques to provide comprehensive surveillance infrastructure mapping across communities.

## Features

### Current Implementation
- **Dynamic Geographic Coverage**: Interactive selection of countries, states/provinces using OpenStreetMap data
- **WiFi Detection**: WiGLE database integration for surveillance devices broadcasting WiFi signals
- **Multi-Vendor Support**: Configurable BSSID prefix detection for various ALPR manufacturers
- **Interactive Selection**: Menu-driven geographic area selection with administrative boundary support
- **Multiple Output Formats**: JSON, CSV, and KML for analysis and mapping platforms
- **Smart Caching**: OSM boundary data caching for improved performance

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
- **Global Support**: Any country with OpenStreetMap administrative boundary data
- **Dynamic Boundaries**: No static ZIP code files - uses live OSM data
- **Flexible Selection**: Single or multiple administrative areas
- **Cached Performance**: Smart caching of boundary data for faster subsequent searches

### External Data Integration
- **WiGLE.net**: Community WiFi and Bluetooth database for device discovery
- **OpenStreetMap**: Geographic data and community mapping platform
- **DeFlock.me**: Community ALPR mapping project integration
- **EFF Atlas of Surveillance**: Cross-reference with known surveillance deployments

## Installation

### Prerequisites
- Python 3.7 or higher
- WiGLE.net API account and token

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/PoppaShell/flockfinder.git
   cd flockfinder
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

3. Obtain WiGLE API credentials:
   - Visit https://wigle.net/ and create a free account
   - Navigate to your account settings and generate an API token

## Usage

### Basic Operation
```bash
# Run as module
python -m src

# Or run directly (if installed)
flockfinder
```

### Interactive Process
1. **WiGLE API Token** (prompted if not set in environment variables)
2. **Country Selection** from OpenStreetMap data
3. **Administrative Division Selection** (states, provinces, counties)
4. **Automated Processing** with progress indicators

### Environment Variables
```bash
export WIGLE_TOKEN="your_wigle_api_token_here"
```

### Configuration Check
```bash
python -m src.config
```

## Project Structure

```
flockfinder/                    # Repository root
├── README.md
├── pyproject.toml              # Modern Python packaging  
├── .gitignore
├── src/
│   ├── __init__.py            # Package files directly in src/
│   ├── __main__.py            # Entry point for -m execution
│   ├── main.py                # Core application logic
│   ├── wigle_api.py           # WiGLE API integration
│   ├── osm_boundaries.py      # OpenStreetMap boundary handling
│   ├── output_formats.py      # JSON, CSV, KML output
│   └── config.py              # Configuration management
├── config/                    # Configuration files
│   ├── known_bssid_prefixes.json
│   └── known_ssid_prefixes.json
├── output/                    # Generated results
│   ├── surveillance_results_*.json
│   ├── surveillance_export_*.csv
│   └── surveillance_locations_*.kml
└── data/                      # Runtime data
    ├── countries.json         # Cached OSM data (gitignored)
    ├── US_admin_4.json        # Cached boundaries (gitignored)
    └── *.cache                # Other cache files (gitignored)
```

## Output Formats

### JSON Results
Complete search data with metadata:
- Search parameters and timestamps
- Geographic area information
- Full network records with WiGLE data

### CSV Export
Universal format compatible with:
- Google My Maps
- ArcGIS Online
- QGIS
- Excel/LibreOffice

### KML Visualization
Google Earth compatible format with:
- Camera location markers
- Detailed information popups
- Custom surveillance camera icons

## Configuration

### BSSID Prefixes
Edit `config/known_bssid_prefixes.json` to add known MAC address prefixes for surveillance devices.

### SSID Patterns
Edit `config/known_ssid_prefixes.json` to add known WiFi network naming patterns.

## Privacy and Ethics

### Responsible Use
- **Privacy Research**: Understanding surveillance infrastructure deployment
- **Community Awareness**: Informing citizens about local monitoring systems
- **Academic Study**: Supporting research into surveillance networks
- **Transparency Advocacy**: Promoting informed policy discussions

### Data Sources
All detection uses publicly available information:
- **WiGLE Database**: Community-contributed WiFi and Bluetooth observations
- **OpenStreetMap**: Community-maintained geographic boundary data
- **Public Records**: Government transparency documents and contracts

## Contributing

### Geographic Enhancement
- OpenStreetMap boundary improvements
- Administrative division data validation
- International region testing

### Detection Method Development
- **Bluetooth Module**: BLE scanning integration with WiGLE data
- **Public Records Automation**: FOIA processing and contract analysis tools
- **Visual Recognition**: Computer vision pipelines for imagery analysis

### Community Support
- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions and improvements
- **Documentation**: Guide improvements and translations

## Development

### Development Installation
```bash
# Clone and install with development dependencies
git clone https://github.com/PoppaShell/flockfinder.git
cd flockfinder
pip install -e ".[dev]"
```

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black src/
flake8 src/
```

## Legal Notice

This project operates within legal boundaries using only publicly available information. Users are responsible for ensuring compliance with local laws and regulations.

## Support

- **Issues**: GitHub issue tracker for bugs and feature requests
- **Discussions**: GitHub discussions for questions and community support
- **Documentation**: Comprehensive guides and API documentation

## License

Open source project supporting transparency and privacy research.