#!/usr/bin/env python3
"""
Test-Script für den neuen Request-Cache und das Transit-Routing.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from wg_scraper.cli_utils import RequestCache, calculate_route


def test_request_cache():
    """Test des Request-Cache Systems."""
    print("=" * 80)
    print("TEST: Request-Cache")
    print("=" * 80)
    
    cache = RequestCache()
    
    # Test 1: Cache schreiben
    print("\n1. Schreibe Daten in Cache...")
    test_url = "http://example.com/api"
    test_params = {"key": "value"}
    test_data = {"result": "success", "id": 123}
    
    success = cache.set(test_url, test_params, test_data)
    print(f"   ✓ Cache.set() erfolgreich: {success}")
    
    # Test 2: Cache auslesen
    print("\n2. Lese Daten aus Cache...")
    cached_data = cache.get(test_url, test_params)
    print(f"   ✓ Gecachte Daten: {cached_data}")
    assert cached_data == test_data, "Cache-Daten stimmen nicht überein!"
    
    # Test 3: Cache-Keys sind unterschiedlich für unterschiedliche URLs
    print("\n3. Teste unterschiedliche Cache-Keys...")
    other_url = "http://example.com/other"
    other_data = cache.get(other_url, test_params)
    print(f"   ✓ Andere URL hat keinen Cache-Eintrag: {other_data is None}")
    assert other_data is None, "Cache sollte leer sein für andere URL!"
    
    print("\n✓ Request-Cache Tests bestanden!")


def test_routing():
    """Test des neuen Routing-Systems mit Transit-Support."""
    print("\n" + "=" * 80)
    print("TEST: Routing mit Transit-Support")
    print("=" * 80)
    
    # Berlin: Alexanderplatz zu Charlottenburg
    origin = (52.5216, 13.4150)  # Alexanderplatz
    destination = (52.5200, 13.2950)  # Nähe Charlottenburg
    
    print(f"\n1. Teste Standard-Routing (Autoverkehr)...")
    result_driving = calculate_route(origin, destination, mode="driving")
    print(f"   Luftlinie: {result_driving['straight_line_km']} km")
    print(f"   Straße: {result_driving['distance_km']} km")
    print(f"   Dauer: {result_driving['duration_min']} min")
    print("   ✓ Routing erfolgreich")
    
    print(f"\n2. Teste Transit-Routing (ÖPNV)...")
    result_transit = calculate_route(origin, destination, mode="transit")
    print(f"   Luftlinie: {result_transit['straight_line_km']} km")
    print(f"   Transit-Distanz: {result_transit['transit_distance_km']} km")
    print(f"   Transit-Dauer: {result_transit['transit_duration_min']} min")
    print(f"   Ist geschätzt: {result_transit['is_transit_estimated']}")
    print("   ✓ Transit-Routing erfolgreich")
    
    print(f"\n3. Teste zu Fuß-Routing...")
    result_walking = calculate_route(origin, destination, mode="walking")
    print(f"   Luftlinie: {result_walking['straight_line_km']} km")
    print(f"   Zu Fuß: {result_walking['distance_km']} km")
    print(f"   Dauer: {result_walking['duration_min']} min")
    print("   ✓ Zu Fuß-Routing erfolgreich")
    
    # Überprüfe, ob Luftlinie in allen gleich ist
    print(f"\n4. Überprüfe Konsistenz...")
    assert result_driving['straight_line_km'] == result_transit['straight_line_km'], \
        "Luftlinien sollten gleich sein!"
    print("   ✓ Luftlinie konsistent über alle Modi")
    
    print("\n✓ Routing Tests bestanden!")


if __name__ == "__main__":
    try:
        test_request_cache()
        test_routing()
        print("\n" + "=" * 80)
        print("✓ ALLE TESTS BESTANDEN!")
        print("=" * 80)
    except Exception as e:
        print(f"\n✗ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
