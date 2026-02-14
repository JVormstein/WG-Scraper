"""
Utilities für die CLI - Filter-Parsing und Routing.
"""

import re
import logging
import json
import csv
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
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


def export_listings(
    listings: List[Dict[str, Any]],
    output_path: str,
    format_type: Optional[str] = None,
    verbose: int = 0,
) -> bool:
    """
    Exportiert Listings in eine Datei.
    
    Args:
        listings: Liste von Listing-Dictionaries
        output_path: Pfad zur Ausgabe-Datei
        format_type: Format ('txt', 'csv', 'json'). Wenn None, wird aus Dateiendung abgeleitet.
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        path = Path(output_path)
        
        # Format aus Dateiendung ableiten wenn nicht angegeben
        if format_type is None:
            format_type = path.suffix.lstrip('.').lower()
            if format_type not in ['txt', 'csv', 'json']:
                format_type = 'txt'
        
        # Je nach Format exportieren
        if format_type == 'json':
            return _export_json(listings, path, verbose)
        elif format_type == 'csv':
            return _export_csv(listings, path, verbose)
        else:  # txt
            return _export_txt(listings, path, verbose)
            
    except Exception as e:
        _logger.error(f"Fehler beim Export: {e}")
        return False


def _export_json(listings: List[Dict[str, Any]], path: Path, verbose: int) -> bool:
    """Exportiert als JSON."""
    try:
        filtered = [_filter_listing_fields(listing, verbose) for listing in listings]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, indent=2, ensure_ascii=False, default=str)
        _logger.info(f"JSON exportiert nach: {path}")
        return True
    except Exception as e:
        _logger.error(f"JSON-Export fehlgeschlagen: {e}")
        return False


def _export_csv(listings: List[Dict[str, Any]], path: Path, verbose: int) -> bool:
    """Exportiert als CSV."""
    try:
        if not listings:
            return False

        filtered = [_filter_listing_fields(listing, verbose) for listing in listings]
        fieldnames = _listing_field_order(verbose)
        
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered)
        
        _logger.info(f"CSV exportiert nach: {path}")
        return True
    except Exception as e:
        _logger.error(f"CSV-Export fehlgeschlagen: {e}")
        return False


def _export_txt(listings: List[Dict[str, Any]], path: Path, verbose: int) -> bool:
    """Exportiert als Text (lesbar)."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"WG-Gesucht Scraper Export\n")
            f.write(f"Anzahl Anzeigen: {len(listings)}\n")
            f.write("="*80 + "\n\n")
            
            for i, listing in enumerate(listings, 1):
                f.write(f"{i}. {listing.get('title', 'N/A')}\n")
                f.write(f"   Stadt: {listing.get('city', 'N/A')}")
                if listing.get('district'):
                    f.write(f" ({listing['district']})")
                f.write("\n")

                f.write(f"   Größe: {listing.get('size', 'N/A')} m² | ")
                f.write(f"Miete: {listing.get('rent', 'N/A')} €\n")
                f.write(f"   Verfügbar ab: {listing.get('available_from', 'N/A')}\n")

                if listing.get('price_per_sqm') is not None:
                    f.write(f"   Preis pro m2: {listing.get('price_per_sqm')} €")
                    if listing.get('avg_ppm_diff') is not None:
                        f.write(f" | Delta avg/m2: {listing.get('avg_ppm_diff')} €")
                    if listing.get('rent_index_diff') is not None:
                        f.write(f" | Delta Mietspiegel: {listing.get('rent_index_diff')} €")
                    f.write("\n")

                if verbose >= 1:
                    if listing.get('available_until'):
                        f.write(f"   Verfügbar bis: {listing.get('available_until', 'N/A')}\n")

                    if listing.get('flatmates'):
                        detail_parts = []
                        if listing.get('flatmates_female') is not None:
                            detail_parts.append(f"{listing['flatmates_female']}w")
                        if listing.get('flatmates_male') is not None:
                            detail_parts.append(f"{listing['flatmates_male']}m")
                        if listing.get('flatmates_diverse') is not None:
                            detail_parts.append(f"{listing['flatmates_diverse']}d")
                        if listing.get('rooms_free') is not None:
                            detail_parts.append(f"{listing['rooms_free']} frei")
                        if listing.get('flatmate_details') and not detail_parts:
                            detail_parts.append(listing['flatmate_details'])

                        f.write(f"   WG-Größe: {listing['flatmates']}er WG")
                        if detail_parts:
                            f.write(f" ({', '.join(detail_parts)})")
                        f.write("\n")

                    if listing.get('room_type'):
                        f.write(f"   Zimmerart: {listing.get('room_type', 'N/A')}\n")

                    if listing.get('online_since'):
                        f.write(f"   Online seit: {listing.get('online_since', 'N/A')}\n")

                if verbose >= 2:
                    if listing.get('description'):
                        desc = listing['description']
                        if len(desc) > 200:
                            desc = desc[:200] + "..."
                        f.write(f"   Beschreibung: {desc}\n")

                    if listing.get('features'):
                        f.write(f"   Features: {listing.get('features', 'N/A')}\n")

                    if listing.get('contact_name'):
                        f.write(f"   Kontakt: {listing.get('contact_name', 'N/A')}\n")

                    f.write(f"   DB-ID: {listing.get('id', 'N/A')} | Listing-ID: {listing.get('listing_id', 'N/A')}\n")
                    f.write(f"   Gescrapt am: {listing.get('scraped_at', 'N/A')}\n")
                    f.write(f"   Erstellt am: {listing.get('created_at', 'N/A')}\n")

                f.write(f"   URL: {listing.get('url', 'N/A')}\n")
                f.write("-"*80 + "\n\n")
        
        _logger.info(f"TXT exportiert nach: {path}")
        return True
    except Exception as e:
        _logger.error(f"TXT-Export fehlgeschlagen: {e}")
        return False


def export_routes(
    results: List[Dict[str, Any]],
    output_path: str,
    destination: str,
    mode: str,
    format_type: Optional[str] = None,
    verbose: int = 0,
) -> bool:
    """
    Exportiert Routen-Ergebnisse in eine Datei.
    
    Args:
        results: Liste von Results mit 'listing' und 'route' Keys
        output_path: Pfad zur Ausgabe-Datei
        destination: Ziel-Adresse
        mode: Verkehrsmittel
        format_type: Format ('txt', 'csv', 'json')
        
    Returns:
        True bei Erfolg
    """
    try:
        path = Path(output_path)
        
        if format_type is None:
            format_type = path.suffix.lstrip('.').lower()
            if format_type not in ['txt', 'csv', 'json']:
                format_type = 'txt'
        
        if format_type == 'json':
            return _export_routes_json(results, path, destination, mode, verbose)
        elif format_type == 'csv':
            return _export_routes_csv(results, path, destination, mode, verbose)
        else:
            return _export_routes_txt(results, path, destination, mode, verbose)
            
    except Exception as e:
        _logger.error(f"Fehler beim Routen-Export: {e}")
        return False


def _export_routes_json(
    results: List[Dict[str, Any]],
    path: Path,
    destination: str,
    mode: str,
    verbose: int,
) -> bool:
    """Exportiert Routen als JSON."""
    try:
        filtered_results = []
        for result in results:
            filtered_results.append({
                'listing': _filter_listing_fields(result['listing'], verbose),
                'route': result['route']
            })

        export_data = {
            'destination': destination,
            'mode': mode,
            'count': len(results),
            'results': filtered_results
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        _logger.info(f"Routen-JSON exportiert nach: {path}")
        return True
    except Exception as e:
        _logger.error(f"Routen-JSON-Export fehlgeschlagen: {e}")
        return False


def _export_routes_csv(
    results: List[Dict[str, Any]],
    path: Path,
    destination: str,
    mode: str,
    verbose: int,
) -> bool:
    """Exportiert Routen als CSV."""
    try:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = _route_field_order(verbose)
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                listing = result['listing']
                route = result['route']
                
                filtered = _filter_listing_fields(listing, verbose)
                row = dict(filtered)
                row.update({
                    'straight_line_km': route.get('straight_line_km', ''),
                    'distance_km': route.get('distance_km', ''),
                    'duration_min': route.get('duration_min', '')
                })
                
                writer.writerow(row)
        
        _logger.info(f"Routen-CSV exportiert nach: {path}")
        return True
    except Exception as e:
        _logger.error(f"Routen-CSV-Export fehlgeschlagen: {e}")
        return False


def _export_routes_txt(
    results: List[Dict[str, Any]],
    path: Path,
    destination: str,
    mode: str,
    verbose: int,
) -> bool:
    """Exportiert Routen als Text."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"WG-Gesucht Scraper - Routen-Analyse\n")
            f.write(f"Ziel: {destination}\n")
            f.write(f"Verkehrsmittel: {mode}\n")
            f.write(f"Anzahl Ergebnisse: {len(results)}\n")
            f.write("="*80 + "\n\n")
            
            for i, result in enumerate(results, 1):
                listing = result['listing']
                route = result['route']

                f.write(f"{i}. {listing.get('title', 'N/A')}\n")
                f.write(f"   {listing.get('city', 'N/A')}")
                if listing.get('district'):
                    f.write(f" - {listing['district']}")
                f.write("\n")

                f.write(f"   Miete: {listing.get('rent', 'N/A')} € | ")
                f.write(f"Größe: {listing.get('size', 'N/A')} m²\n")

                if listing.get('price_per_sqm') is not None:
                    f.write(f"   Preis pro m2: {listing.get('price_per_sqm')} €")
                    if listing.get('avg_ppm_diff') is not None:
                        f.write(f" | Delta avg/m2: {listing.get('avg_ppm_diff')} €")
                    if listing.get('rent_index_diff') is not None:
                        f.write(f" | Delta Mietspiegel: {listing.get('rent_index_diff')} €")
                    f.write("\n")

                f.write(f"   Luftlinie: {route['straight_line_km']} km")
                if route['distance_km']:
                    f.write(f" | {mode.title()}: {route['distance_km']} km")
                if route['duration_min']:
                    f.write(f" (~{route['duration_min']} min)")
                f.write("\n")

                if verbose >= 1:
                    if listing.get('available_from'):
                        f.write(f"   Verfügbar ab: {listing.get('available_from', 'N/A')}")
                        if listing.get('available_until'):
                            f.write(f" bis {listing.get('available_until', 'N/A')}")
                        f.write("\n")

                    if listing.get('flatmates'):
                        detail_parts = []
                        if listing.get('flatmates_female') is not None:
                            detail_parts.append(f"{listing['flatmates_female']}w")
                        if listing.get('flatmates_male') is not None:
                            detail_parts.append(f"{listing['flatmates_male']}m")
                        if listing.get('flatmates_diverse') is not None:
                            detail_parts.append(f"{listing['flatmates_diverse']}d")
                        if listing.get('rooms_free') is not None:
                            detail_parts.append(f"{listing['rooms_free']} frei")
                        if listing.get('flatmate_details') and not detail_parts:
                            detail_parts.append(listing['flatmate_details'])

                        f.write(f"   WG-Größe: {listing['flatmates']}er WG")
                        if detail_parts:
                            f.write(f" ({', '.join(detail_parts)})")
                        f.write("\n")

                    if listing.get('room_type'):
                        f.write(f"   Zimmerart: {listing.get('room_type', 'N/A')}\n")

                    if listing.get('online_since'):
                        f.write(f"   Online seit: {listing.get('online_since', 'N/A')}\n")

                if verbose >= 2:
                    if listing.get('description'):
                        desc = listing['description']
                        if len(desc) > 200:
                            desc = desc[:200] + "..."
                        f.write(f"   Beschreibung: {desc}\n")

                    if listing.get('features'):
                        f.write(f"   Features: {listing.get('features', 'N/A')}\n")

                    if listing.get('contact_name'):
                        f.write(f"   Kontakt: {listing.get('contact_name', 'N/A')}\n")

                    f.write(f"   DB-ID: {listing.get('id', 'N/A')} | Listing-ID: {listing.get('listing_id', 'N/A')}\n")
                    f.write(f"   Gescrapt am: {listing.get('scraped_at', 'N/A')}\n")
                    f.write(f"   Erstellt am: {listing.get('created_at', 'N/A')}\n")

                f.write(f"   URL: {listing.get('url', 'N/A')}\n")
                f.write("-"*80 + "\n\n")
        
        _logger.info(f"Routen-TXT exportiert nach: {path}")
        return True
    except Exception as e:
        _logger.error(f"Routen-TXT-Export fehlgeschlagen: {e}")
        return False


def _listing_field_order(verbose: int) -> List[str]:
    """Definiert die Spaltenreihenfolge fuer Listing-Exports."""
    base_fields = [
        'title', 'city', 'district', 'size', 'rent', 'available_from', 'url',
        'price_per_sqm', 'avg_ppm_diff', 'rent_index_diff'
    ]

    detail_fields = [
        'available_until', 'flatmates', 'flatmate_details', 'flatmates_female',
        'flatmates_male', 'flatmates_diverse', 'rooms_free', 'room_type', 'online_since'
    ]

    meta_fields = [
        'description', 'features', 'contact_name', 'images',
        'id', 'listing_id', 'scraped_at', 'created_at'
    ]

    fields = list(base_fields)
    if verbose >= 1:
        fields.extend(detail_fields)
    if verbose >= 2:
        fields.extend(meta_fields)
    return fields


def _route_field_order(verbose: int) -> List[str]:
    """Definiert die Spaltenreihenfolge fuer Routen-CSV-Export."""
    fields = _listing_field_order(verbose)
    fields.extend(['straight_line_km', 'distance_km', 'duration_min'])
    return fields


def _filter_listing_fields(listing: Dict[str, Any], verbose: int) -> Dict[str, Any]:
    """Reduziert Listing-Felder basierend auf Verbosity-Level."""
    filtered = {
        'title': listing.get('title'),
        'city': listing.get('city'),
        'district': listing.get('district'),
        'size': listing.get('size'),
        'rent': listing.get('rent'),
        'available_from': listing.get('available_from'),
        'url': listing.get('url'),
        'price_per_sqm': listing.get('price_per_sqm'),
        'avg_ppm_diff': listing.get('avg_ppm_diff'),
        'rent_index_diff': listing.get('rent_index_diff')
    }

    if verbose >= 1:
        filtered.update({
            'available_until': listing.get('available_until'),
            'flatmates': listing.get('flatmates'),
            'flatmate_details': listing.get('flatmate_details'),
            'flatmates_female': listing.get('flatmates_female'),
            'flatmates_male': listing.get('flatmates_male'),
            'flatmates_diverse': listing.get('flatmates_diverse'),
            'rooms_free': listing.get('rooms_free'),
            'room_type': listing.get('room_type'),
            'online_since': listing.get('online_since')
        })

    if verbose >= 2:
        filtered.update({
            'description': listing.get('description'),
            'features': listing.get('features'),
            'contact_name': listing.get('contact_name'),
            'images': listing.get('images'),
            'id': listing.get('id'),
            'listing_id': listing.get('listing_id'),
            'scraped_at': listing.get('scraped_at'),
            'created_at': listing.get('created_at')
        })

    return filtered
