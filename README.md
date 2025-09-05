# FlockFinder

> Automated detection and mapping of ALPR cameras using open source intelligence

## Overview

FlockFinder systematically locates ALPR (Automated License Plate Recognition) cameras at scale using WiFi database intelligence. The project searches Wigle.net for devices with known BSSID prefixes and SSID patterns, then outputs results in multiple formats for mapping and analysis.

## Goals

- **Scale Detection**: Find ALPR cameras efficiently across large geographic areas
- **WiFi Intelligence**: Use Wigle.net database to identify camera WiFi signatures
- **Multiple Output Formats**: Generate JSON, CSV, and KML files for various mapping platforms
- **Geographic Filtering**: Focus searches on specific regions using ZIP code databases

## How It Works

### Detection Method

- **BSSID Search**: Query Wigle database for known MAC address prefixes used by ALPR devices
- **SSID Patterns**: Search for device-specific naming conventions like “Flock-*”
- **Geographic Filtering**: Filter results by ZIP codes for specific metro areas (DFW, Houston)
- **Multi-Format Export**: Output results as JSON, CSV, and KML for different mapping tools

## Quick Start

### Prerequisites

- Python 3.7+
- Wigle.net account with API access
- OpenStreetMap account for submitting new findings

### Setup

```bash
git clone https://github.com/PoppaShell/flockfinder.git
cd flockfinder
```

### Basic Usage

```bash
# Run the scanner (will prompt for Wigle API token)
python flockfinder.py
```

### Interactive Menu

The scanner provides an interactive interface:

```
Select state area to scan:
  1. Texas
```
```
Select counties to scan:
  1. Collin County - 45 ZIP codes (Plano, Frisco, McKinney)
  2. Dallas County - 78 ZIP codes (Dallas, Irving, Garland)
  3. Denton County - 34 ZIP codes (Denton, Lewisville, Flower Mound)
  ...
  16. All counties (entire state)
```

## Project Structure

```
flockfinder/
├── README.md
├── wigle_flock_scanner.py       # Main scanner script
├── known_bssid_prefixes.json    # Device MAC address database
├── geographic_registry.json     # County and ZIP code registry
└── geographic_data/
    ├── tx_collin_zips.json      # Collin County ZIP codes
    ├── tx_dallas_zips.json      # Dallas County ZIP codes
    ├── tx_denton_zips.json      # Denton County ZIP codes
    ├── tx_ellis_zips.json       # Ellis County ZIP codes
    ├── tx_harris_zips.json      # Harris County ZIP codes
    ├── tx_fortbend_zips.json    # Fort Bend County ZIP codes
    ├── tx_montgomery_zips.json  # Montgomery County ZIP codes
    ├── tx_galveston_zips.json   # Galveston County ZIP codes
    ├── tx_rockwall_zips.json    # Rockwall County ZIP codes
    ├── tx_tarrant_zips.json     # Tarrant County ZIP codes
    └── tx_wise_zips.json        # Wise County ZIP codes
```

## Configuration

### Device Database

The `known_bssid_prefixes.json` file contains MAC address prefixes:

```json
{
  "bssids": [
    "00:F4:8D", "08:3A:88", "14:5A:FC", "3C:91:80",
    "62:DD:4C", "70:C9:4E", "74:4C:A1", "80:30:49"
  ]
}
```

### Geographic Data

ZIP code databases organized by county with metadata:

```json
{
  "75024": {
    "city": "Plano", 
    "county": "Collin",
    "state": "TX"
  }
}
```

## Output Formats

### JSON Results

```json
{
  "search_metadata": {
    "timestamp": "2025-09-04T12:00:00Z",
    "counties_searched": ["Dallas", "Collin"],
    "total_results": 25
  },
  "devices": [
    {
      "trilat": 32.7767,
      "trilong": -96.7970,
      "ssid": "Flock-ABC123",
      "netid": "08:3A:88:XX:XX:XX",
      "city": "Dallas",
      "county": "Dallas"
    }
  ]
}
```

### CSV Export

Universal format for spreadsheet analysis with columns:

- Latitude, Longitude, SSID, BSSID, City, County, State

### KML Export

Geographic markup for mapping platforms (Google Earth, ArcGIS, QGIS)

## Resources

- [Wigle.net](https://wigle.net) - WiFi database and API
- [DeFlock.me](https://deflock.me) - ALPR camera location database
- [OpenStreetMap](https://openstreetmap.org) - Collaborative mapping platform