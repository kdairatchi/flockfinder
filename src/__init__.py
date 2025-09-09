"""
FlockFinder Package
==================
ALPR surveillance camera detection using WiGLE database and OpenStreetMap boundaries

This package provides tools for systematically locating surveillance cameras
by analyzing WiFi signatures and geographic data.
"""

__version__ = "2.0.0"
__author__ = "FlockFinder Project"
__description__ = "ALPR surveillance camera detection using open source intelligence"

# Import main components for easy access
from .main import main
from .config import setup_project_structure, print_configuration_status

# Package exports
__all__ = [
    'main',
    'setup_project_structure', 
    'print_configuration_status'
]