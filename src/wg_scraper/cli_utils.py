"""
Utilities für die CLI - Filter-Parsing und Routing.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests

_logger = logging.getLogger(__name__)


def parse_filters(filter_string: Optional[str]) -> Dict[str, Any]:
    """
    Parst Filter-String in Dictionary.
    
    Format: "size>20;rent<500;city=Berlin"
    
    Unterstützte Operatoren: =, >, <, >=, <=, !=
    
    Args:
        filter_string: Filter-String mit Semikolon-Trennung
        
    Returns:
        Dictionary mit Filtern
    """
    if not filter_string:
        return {}
    
    filters = {}
    
    # Split by semicolon
    parts = filter_string.split(';')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Finde Operator
        match = re.match(r'(\w+)(>=|<=|!=|>|<|=)(.+)', part)
        if not match:
            _logger.warning(f"Ungültiger Filter: {part}")
            continue
        
        field, operator, value = match.groups()
        value = value.strip()
        
        # Konvertiere Wert
        try:
            # Versuche als Zahl
            if '.' in value:
                value = float(value)
            else:
                value = int(value)
        except ValueError:
            # Bleibt String
            pass
        
        # Speichere mit Operator
        if operator == '=':
            filters[field] = value
        else:
            filters[f"{field}{operator}"] = value
    
    return filters


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Konvertiert Adresse in Koordinaten.
    
    Args:
        address: Adresse als String
        
    Returns:
        Tuple (latitude, longitude) oder None
    """
    try:
        geolocator = Nominatim(user_agent="wg-scraper")
        location = geolocator.geocode(address, timeout=10)
        
        if location:
            return (location.latitude, location.longitude)
        
        _logger.warning(f"Adresse nicht gefunden: {address}")
        return None
        
    except Exception as e:
        _logger.error(f"Fehler beim Geocoding: {e}")
        return None


def calculate_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    mode: str = "driving"
) -> Optional[Dict[str, Any]]:
    """
    Berechnet Route und Distanz.
    
    Args:
        origin: Start-Koordinaten (lat, lon)
        destination: Ziel-Koordinaten (lat, lon)
        mode: Verkehrsmittel ('driving', 'transit', 'walking', 'cycling')
        
    Returns:
        Dictionary mit 'distance_km', 'duration_min', 'straight_line_km'
    """
    try:
        # Luftlinie berechnen (immer verfügbar)
        straight_line = geodesic(origin, destination).kilometers
        
        result = {
            'straight_line_km': round(straight_line, 2),
            'distance_km': None,
            'duration_min': None
        }
        
        # Versuche Routing über OSRM (kostenlos, keine API-Key nötig)
        # Unterstützt: car, bike, foot
        osrm_mode = {
            'driving': 'car',
            'car': 'car',
            'cycling': 'bike',
            'bike': 'bike',
            'walking': 'foot',
            'foot': 'foot'
        }.get(mode.lower(), 'car')
        
        url = f"http://router.project-osrm.org/route/v1/{osrm_mode}/{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
        params = {
            'overview': 'false',
            'steps': 'false'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 'Ok' and data.get('routes'):
                route = data['routes'][0]
                result['distance_km'] = round(route['distance'] / 1000, 2)
                result['duration_min'] = round(route['duration'] / 60, 1)
        else:
            _logger.warning(f"OSRM Routing fehlgeschlagen: {response.status_code}")
        
        return result
        
    except Exception as e:
        _logger.error(f"Fehler bei Routing-Berechnung: {e}")
        return {
            'straight_line_km': round(straight_line, 2) if 'straight_line' in locals() else None,
            'distance_km': None,
            'duration_min': None
        }
