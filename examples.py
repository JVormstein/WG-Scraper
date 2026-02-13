#!/usr/bin/env python
"""
Beispiel-Script für die programmatische Nutzung des WG-Scrapers.

Zeigt, wie die Scraper-Klassen direkt verwendet werden können
ohne die CLI.
"""

import logging
from wg_scraper.scraper import WGScraper
from wg_scraper.database import Database
from wg_scraper.models import WGListing

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s:%(name)s:%(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_scraping():
    """Einfaches Scraping-Beispiel."""
    logger.info("=== Beispiel 1: Basis-Scraping ===")
    
    # Scraper initialisieren
    scraper = WGScraper(delay=1.5)
    
    # URL zum Scrapen (Beispiel - URL anpassen!)
    url = "https://www.wg-gesucht.de/wg-zimmer-in-Berlin.8.0.1.0.html"
    
    # Erste Seite scrapen (max_pages=1)
    listings = list(scraper.scrape_search_results(url, max_pages=1))
    
    logger.info(f"Gefundene Listings: {len(listings)}")
    
    # Erste 3 Listings ausgeben
    for i, listing in enumerate(listings[:3], 1):
        logger.info(f"\n{i}. {listing}")
    
    scraper.close()


def example_database_usage():
    """Beispiel für Datenbank-Operationen."""
    logger.info("\n=== Beispiel 2: Datenbank-Nutzung ===")
    
    # Datenbank initialisieren
    db = Database("example_data.db")
    db.init_db()
    
    # Beispiel-Listing erstellen
    listing = WGListing(
        listing_id="12345",
        url="https://example.com/listing/12345",
        title="Schönes WG-Zimmer in Berlin-Mitte",
        city="Berlin",
        district="Mitte",
        size=20.0,
        rent=450.0,
        room_type="WG-Zimmer",
    )
    
    # In Datenbank speichern
    saved = db.save_listing(listing)
    logger.info(f"Listing gespeichert: {saved}")
    
    # Listing abrufen
    retrieved = db.get_listing("12345")
    logger.info(f"Abgerufen: {retrieved}")
    
    # Statistiken
    stats = db.get_statistics()
    logger.info(f"Statistiken: {stats}")
    
    db.close()


def example_context_manager():
    """Beispiel mit Context Manager."""
    logger.info("\n=== Beispiel 3: Context Manager ===")
    
    # Database als Context Manager
    with Database("example_data.db") as db:
        db.init_db()
        
        listings = db.get_listings(limit=5)
        logger.info(f"Gefundene Listings in DB: {len(listings)}")
        
        for listing in listings:
            logger.info(f"  - {listing['title']} in {listing['city']}")
    
    # Verbindung wird automatisch geschlossen


def example_custom_listing():
    """Beispiel: Eigene Listings erstellen und speichern."""
    logger.info("\n=== Beispiel 4: Custom Listings ===")
    
    # Mehrere Listings erstellen
    listings = [
        WGListing(
            listing_id=f"test_{i}",
            url=f"https://example.com/{i}",
            title=f"WG-Zimmer #{i}",
            city=city,
            rent=300 + i * 50,
            size=15 + i * 5
        )
        for i, city in enumerate(["Berlin", "München", "Hamburg"], 1)
    ]
    
    # In Datenbank speichern
    with Database("example_data.db") as db:
        db.init_db()
        
        for listing in listings:
            db.save_listing(listing)
            logger.info(f"Gespeichert: {listing.title} - {listing.city}")
        
        # Alle Listings abrufen
        all_listings = db.get_listings(limit=10)
        logger.info(f"\nGesamt in DB: {len(all_listings)} Listings")


def example_filtering():
    """Beispiel: Listings filtern."""
    logger.info("\n=== Beispiel 5: Filtern ===")
    
    with Database("example_data.db") as db:
        db.init_db()
        
        # Nach Stadt filtern
        berlin_listings = db.get_listings(city="Berlin", limit=5)
        logger.info(f"Listings in Berlin: {len(berlin_listings)}")
        
        # Nach Größe filtern
        large_rooms = db.get_listings(min_size=20, limit=5)
        logger.info(f"Große Zimmer (>20m²): {len(large_rooms)}")
        
        # Nach Miete filtern
        affordable = db.get_listings(max_rent=400, limit=5)
        logger.info(f"Günstige Zimmer (<400€): {len(affordable)}")


if __name__ == "__main__":
    logger.info("WG-Scraper Beispiel-Script")
    logger.info("=" * 50)
    
    try:
        # Beispiel 1: Basis-Scraping (nur wenn implementiert)
        # example_basic_scraping()
        logger.info("⚠️  Beispiel 1 übersprungen - Scraping noch nicht implementiert")
        
        # Beispiel 2: Datenbank
        example_database_usage()
        
        # Beispiel 3: Context Manager
        example_context_manager()
        
        # Beispiel 4: Custom Listings
        example_custom_listing()
        
        # Beispiel 5: Filtern
        example_filtering()
        
        logger.info("\n" + "=" * 50)
        logger.info("✓ Alle Beispiele erfolgreich ausgeführt!")
        logger.info("Testdatenbank: example_data.db")
        
    except Exception as e:
        logger.error(f"Fehler: {e}", exc_info=True)
