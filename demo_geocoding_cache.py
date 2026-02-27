#!/usr/bin/env python3
"""
Demonstriert die Cache-Funktionalität der geocode_address Funktion.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from wg_scraper.cli_utils import (
    geocode_address,
    clear_geocoding_cache,
    get_geocoding_cache_stats
)


def main():
    print("=" * 80)
    print("Geocoding Cache Demonstration")
    print("=" * 80)
    
    # Zeige initiale Cache-Statistiken
    print("\n1. Initiale Cache-Statistiken:")
    stats = get_geocoding_cache_stats()
    print(f"   Cache-Verzeichnis: {stats['cache_dir']}")
    print(f"   Gecachte Einträge: {stats['cached_entries']}")
    print(f"   Cache-Größe: {stats['cache_size_mb']} MB")
    
    # Test-Adressen
    test_addresses = [
        "Berlin, Deutschland",
        "Stuttgart, Deutschland",
        "Berlin, Deutschland",  # Duplicate - sollte aus Cache kommen
    ]
    
    print("\n2. Geocoding mit Cache:")
    print("   " + "-" * 76)
    
    for i, address in enumerate(test_addresses, 1):
        print(f"\n   Request {i}: '{address}'")
        
        # Zeige Cache-Status vor der Anfrage
        stats_before = get_geocoding_cache_stats()
        
        start_time = time.time()
        coords = geocode_address(address)
        elapsed_time = time.time() - start_time
        
        # Zeige Cache-Status nach der Anfrage
        stats_after = get_geocoding_cache_stats()
        
        if coords:
            print(f"   ✓ Koordinaten: ({coords[0]:.4f}, {coords[1]:.4f})")
        else:
            print(f"   ✗ Nicht gefunden")
        
        print(f"   ⏱  Zeit: {elapsed_time:.3f}s")
        
        # Zeige ob aus Cache geladen
        if stats_after['cached_entries'] > stats_before['cached_entries']:
            print(f"   📝 NEU gecacht (Cache: {stats_before['cached_entries']} → {stats_after['cached_entries']})")
        else:
            print(f"   💾 Aus CACHE geladen (keine neue Einträge)")
    
    # Finale Cache-Statistiken
    print("\n" + "=" * 80)
    print("3. Finale Cache-Statistiken:")
    stats = get_geocoding_cache_stats()
    print(f"   Cache-Verzeichnis: {stats['cache_dir']}")
    print(f"   Gecachte Einträge: {stats['cached_entries']}")
    print(f"   Cache-Größe: {stats['cache_size_mb']} MB")
    
    # Cache-Bereinigung (optional)
    print("\n" + "=" * 80)
    print("4. Cache-Bereinigung (optional):")
    response = input("   Möchten Sie den Cache leeren? (j/n): ")
    
    if response.lower() in ['j', 'y', 'ja', 'yes']:
        clear_geocoding_cache()
        print("   ✓ Cache geleert")
        stats = get_geocoding_cache_stats()
        print(f"   Gecachte Einträge: {stats['cached_entries']}")
    else:
        print("   Cache wurde NICHT geleert")
    
    print("\n" + "=" * 80)
    print("Zusammenfassung:")
    print("=" * 80)
    print("✓ Die geocode_address() Funktion nutzt automatisch einen Cache")
    print("✓ Cache-Verzeichnis: ~/.wg_scraper_geocoding_cache")
    print("✓ Cache TTL: 7 Tage")
    print("✓ Rate Limiting: Mindestens 1 Sekunde zwischen API-Anfragen")
    print("✓ Bei Cache Hit: Sofortige Rückgabe (< 0.01s)")
    print("✓ Bei Cache Miss: API-Request + Caching (> 1s wegen Rate Limit)")
    print()


if __name__ == "__main__":
    main()
