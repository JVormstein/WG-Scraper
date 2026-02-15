"""
Utilities für die CLI - Filter-Parsing und Routing.
"""

import re
import logging
import json
import csv
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
import hashlib
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests

_logger = logging.getLogger(__name__)


class RequestCache:
    """
    Einfacher Cache für HTTP-Requests, um redundante API-Calls zu vermeiden.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = 24):
        """
        Initialisiert den Cache.
        
        Args:
            cache_dir: Verzeichnis für Cache-Dateien. Wenn None, wird ~/.wg_scraper_cache verwendet.
            ttl_hours: Time-to-live für Cache-Einträge in Stunden (Standard: 24)
        """
        if cache_dir is None:
            cache_dir = Path.home() / '.wg_scraper_cache'
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        _logger.debug(f"RequestCache initialisiert in {self.cache_dir} mit TTL {ttl_hours}h")
    
    def _get_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """
        Generiert einen Cache-Schlüssel aus URL und Parametern.
        
        Args:
            url: Request-URL
            params: Query-Parameter
            
        Returns:
            Cache-Schlüssel (MD5-Hash)
        """
        cache_data = f"{url}|{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _get_cache_file(self, key: str) -> Path:
        """Gibt den Cache-Dateipfad für einen Schlüssel zurück."""
        return self.cache_dir / f"{key}.json"
    
    def get(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Holt einen gecachten Wert, wenn vorhanden und noch gültig.
        
        Args:
            url: Request-URL
            params: Query-Parameter
            
        Returns:
            Gecachte Daten oder None
        """
        key = self._get_cache_key(url, params)
        cache_file = self._get_cache_file(key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Prüfe TTL
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            if datetime.now() - cached_at > self.ttl:
                _logger.debug(f"Cache abgelaufen: {key}")
                cache_file.unlink()
                return None
            
            _logger.debug(f"Cache Hit: {key}")
            return cache_data['data']
            
        except Exception as e:
            _logger.warning(f"Fehler beim Cache-Read: {e}")
            return None
    
    def set(self, url: str, params: Optional[Dict], data: Dict) -> bool:
        """
        Speichert einen Wert im Cache.
        
        Args:
            url: Request-URL
            params: Query-Parameter
            data: Zu cachende Daten
            
        Returns:
            True bei Erfolg
        """
        key = self._get_cache_key(url, params)
        cache_file = self._get_cache_file(key)
        
        try:
            cache_data = {
                'cached_at': datetime.now().isoformat(),
                'url': url,
                'params': params,
                'data': data
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            
            _logger.debug(f"Cache Set: {key}")
            return True
            
        except Exception as e:
            _logger.warning(f"Fehler beim Cache-Write: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Löscht alle Cache-Einträge.
        
        Returns:
            True bei Erfolg
        """
        try:
            for cache_file in self.cache_dir.glob('*.json'):
                cache_file.unlink()
            _logger.info("Cache geleert")
            return True
        except Exception as e:
            _logger.warning(f"Fehler beim Cache-Löschen: {e}")
            return False


# Globale Cache-Instanz
_request_cache = RequestCache()


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
    Berechnet Route und Distanz mit Caching.
    
    Args:
        origin: Start-Koordinaten (lat, lon)
        destination: Ziel-Koordinaten (lat, lon)
        mode: Verkehrsmittel ('driving', 'transit', 'walking', 'cycling')
        
    Returns:
        Dictionary mit:
            - 'straight_line_km': Luftlinie (immer verfügbar)
            - 'distance_km': Straßenentfernung (optional)
            - 'duration_min': Fahrtdauer nach Verkehrsmittel (optional)
            - 'transit_distance_km': Transit-Distanz (nur bei mode='transit')
            - 'transit_duration_min': Transit-Dauer (nur bei mode='transit')
            - 'is_transit_estimated': True wenn Transit-Zeit geschätzt wurde
    """
    try:
        # Luftlinie berechnen (immer verfügbar)
        straight_line = geodesic(origin, destination).kilometers
        
        result = {
            'straight_line_km': round(straight_line, 2),
            'distance_km': None,
            'duration_min': None,
            'transit_distance_km': None,
            'transit_duration_min': None,
            'is_transit_estimated': False
        }
        
        # Transit-Modus: Spezialbehandlung
        if mode.lower() in ['transit', 'öpnv', 'public']:
            return _calculate_transit_route(origin, destination, result)
        
        # Standard-Routing über OSRM (kostenlos, keine API-Key nötig)
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
        
        # Prüfe Cache
        cached_data = _request_cache.get(url, params)
        if cached_data:
            result['distance_km'] = cached_data.get('distance_km')
            result['duration_min'] = cached_data.get('duration_min')
            return result
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 'Ok' and data.get('routes'):
                route = data['routes'][0]
                result['distance_km'] = round(route['distance'] / 1000, 2)
                result['duration_min'] = round(route['duration'] / 60, 1)
                
                # Speichere im Cache
                _request_cache.set(url, params, {
                    'distance_km': result['distance_km'],
                    'duration_min': result['duration_min']
                })
        else:
            _logger.warning(f"OSRM Routing fehlgeschlagen: {response.status_code}")
        
        return result
        
    except Exception as e:
        _logger.error(f"Fehler bei Routing-Berechnung: {e}")
        return {
            'straight_line_km': round(straight_line, 2) if 'straight_line' in locals() else None,
            'distance_km': None,
            'duration_min': None,
            'transit_distance_km': None,
            'transit_duration_min': None,
            'is_transit_estimated': False
        }


def _calculate_transit_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Berechnet Transit-Routen mit Fallback auf Schätzung.
    Versucht zunächst, echte Fahrtdaten von der API zu holen.
    Falls das fehlschlägt, wird eine Schätzung basierend auf Luftlinie verwendet.
    
    Args:
        origin: Start-Koordinaten (lat, lon)
        destination: Ziel-Koordinaten (lat, lon)
        result: Basis-Result mit bereits berechneter Luftlinie
        
    Returns:
        Result mit Transit-Daten (geholt oder geschätzt)
    """
    try:
        # Versuche, echte Transit-Daten zu holen (z.B. von OSRM mit foot-Routing als Proxy)
        # OSRM unterstützt kein echtes Transit-Routing, daher verwenden wir Schätzung
        url = f"http://router.project-osrm.org/route/v1/foot/{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
        params = {'overview': 'false', 'steps': 'false'}
        
        # Prüfe Cache
        cached_data = _request_cache.get(url, params)
        if cached_data:
            result['transit_distance_km'] = cached_data.get('transit_distance_km')
            result['transit_duration_min'] = cached_data.get('transit_duration_min')
            result['is_transit_estimated'] = cached_data.get('is_transit_estimated')
            return result
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 'Ok' and data.get('routes'):
                # Verwende Zu-Fuß-Route als ungefähre Basis für Transit
                route = data['routes'][0]
                # Transit ist typischerweise schneller als zu Fuß, aber mit Wartezeiten
                # Schätzung: ~1.5x Zu-Fuß-Distanz, aber ~0.4x Zu-Fuß-Zeit (mit Wartezeiten)
                result['transit_distance_km'] = round(route['distance'] / 1000 * 1.5, 2)
                result['transit_duration_min'] = round(route['duration'] / 60 * 0.4, 1)
                result['is_transit_estimated'] = True
                
                # Speichere im Cache
                _request_cache.set(url, params, {
                    'transit_distance_km': result['transit_distance_km'],
                    'transit_duration_min': result['transit_duration_min'],
                    'is_transit_estimated': True
                })
                
                _logger.debug(f"Transit-Fahrtzeit geschätzt: {result['transit_duration_min']}min")
                return result
    except Exception as e:
        _logger.debug(f"Transit-Routing fehlgeschlagen, verwende Fallback-Schätzung: {e}")
    
    # Fallback: Schätzung nur aus Luftlinie
    # Durchschnittliche Busgeschwindigkeit: ~20 km/h (inklusive Wartezeiten, Haltestellen)
    straight_line = result['straight_line_km']
    if straight_line:
        # Annahme: ÖPNV-Route ist 20% länger als Luftlinie
        result['transit_distance_km'] = round(straight_line * 1.2, 2)
        # Durchschnittliche ÖPNV-Geschwindigkeit: ~12 km/h (mit Wartezeiten)
        result['transit_duration_min'] = round((straight_line * 1.2) / 12 * 60, 1)
        result['is_transit_estimated'] = True
        _logger.debug(f"Transit-Fahrtzeit aus Luftlinie geschätzt: {result['transit_duration_min']}min")
    
    return result


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
    """Exportiert als CSV mit zusätzlichem Stadt-Feld."""
    try:
        if not listings:
            return False

        filtered = [_filter_listing_fields(listing, verbose) for listing in listings]
        fieldnames = _listing_field_order(verbose)
        
        # Füge Stadt-Feld nach 'city' ein (nur für CSV-Export sichtbar)
        if 'city' in fieldnames:
            city_index = fieldnames.index('city')
            fieldnames.insert(city_index + 1, 'listing_city')
        
        # Extrahiere Stadt aus jedem Listing und füge es als 'listing_city' hinzu
        for listing in filtered:
            listing['listing_city'] = listing.get('city', '')  # Stadt seperiert für CSV
        
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
    """Exportiert Routen als CSV mit zusätzlichem Stadt-Feld."""
    try:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = list(_route_field_order(verbose))
            
            # Füge Stadt-Feld nach 'city' ein (nur für CSV-Export sichtbar)
            if 'city' in fieldnames:
                city_index = fieldnames.index('city')
                fieldnames.insert(city_index + 1, 'listing_city')
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                listing = result['listing']
                route = result['route']
                
                filtered = _filter_listing_fields(listing, verbose)
                row = dict(filtered)
                
                # Füge Stadt-Feld seperat ein
                row['listing_city'] = filtered.get('city', '')
                
                row.update({
                    'straight_line_km': route.get('straight_line_km', ''),
                    'distance_km': route.get('distance_km', ''),
                    'duration_min': route.get('duration_min', ''),
                    'transit_distance_km': route.get('transit_distance_km', ''),
                    'transit_duration_min': route.get('transit_duration_min', ''),
                    'is_transit_estimated': route.get('is_transit_estimated', '')
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
                
                # Zusätzliche Transit-Informationen wenn verfügbar
                if route.get('transit_distance_km'):
                    f.write(f"   Transit: {route['transit_distance_km']} km")
                    if route['transit_duration_min']:
                        f.write(f" (~{route['transit_duration_min']} min)")
                    if route.get('is_transit_estimated'):
                        f.write(" [geschätzt]")
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
    # Getrennte Felder für Luftlinie, Standard-Routing und Transit
    fields.extend([
        'straight_line_km', 
        'distance_km', 
        'duration_min',
        'transit_distance_km',
        'transit_duration_min',
        'is_transit_estimated'
    ])
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
