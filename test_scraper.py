#!/usr/bin/env python
"""
Test-Script für den WG-Scraper.

Testet die Scraping-Funktionalität mit einer echten URL.
"""

import sys
import logging
from wg_scraper.scraper import WGScraper
from wg_scraper.database import Database

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s:%(name)s:%(message)s'
)

logger = logging.getLogger(__name__)


def test_scraper(url: str, max_pages: int = 1):
    """
    Testet den Scraper mit einer URL.
    
    Args:
        url: WG-Gesucht such-URL
        max_pages: Maximale Anzahl Seiten zum Testen
    """
    logger.info("="*80)
    logger.info("WG-Scraper Test")
    logger.info("="*80)
    logger.info(f"URL: {url}")
    logger.info(f"Max Pages: {max_pages}")
    logger.info("")
    
    # Scraper initialisieren
    scraper = WGScraper(delay=1.5)
    
    try:
        # Scraping starten
        listings = list(scraper.scrape_search_results(url, max_pages=max_pages))
        
        logger.info("")
        logger.info("="*80)
        logger.info(f"ERGEBNIS: {len(listings)} Listings gefunden")
        logger.info("="*80)
        logger.info("")
        
        # Erste 3 Listings detailliert ausgeben
        for i, listing in enumerate(listings[:3], 1):
            logger.info(f"{i}. {listing.title}")
            logger.info(f"   ID: {listing.listing_id}")
            logger.info(f"   Stadt: {listing.city} ({listing.district})")
            logger.info(f"   Größe: {listing.size} m²")
            logger.info(f"   Miete: {listing.rent} €")
            logger.info(f"   WG-Größe: {listing.flatmates}er WG")
            logger.info(f"   Mitbewohner: {listing.flatmate_details}")
            logger.info(f"   Verfügbar ab: {listing.available_from}")
            logger.info(f"   URL: {listing.url}")
            logger.info("")
        
        if len(listings) > 3:
            logger.info(f"... und {len(listings) - 3} weitere Listings")
            logger.info("")
        
        # Optional: In Datenbank speichern
        save = input("In Datenbank speichern? (j/n): ").lower().strip()
        if save == 'j':
            db = Database("test_scraping.db")
            db.init_db()
            
            saved = 0
            for listing in listings:
                if db.save_listing(listing):
                    saved += 1
            
            logger.info(f"✓ {saved} Listings in test_scraping.db gespeichert")
            db.close()
        
    except KeyboardInterrupt:
        logger.info("\n\nAbgebrochen durch Benutzer")
    except Exception as e:
        logger.error(f"Fehler beim Scraping: {e}", exc_info=True)
    finally:
        scraper.close()


def test_pagination():
    """Testet den Pagination-Mechanismus."""
    logger.info("="*80)
    logger.info("Test: Pagination-Mechanismus")
    logger.info("="*80)
    
    scraper = WGScraper(delay=0)
    
    test_urls = [
        "https://www.wg-gesucht.de/wg-zimmer-in-Stuttgart.124.0.1.0.html?sort_column=3",
        "https://www.wg-gesucht.de/wg-zimmer-in-Berlin.8.0.1.12.html?filter=1",
        "https://www.wg-gesucht.de/wohnungen-in-Muenchen.90.2.1.5.html",
    ]
    
    for url in test_urls:
        next_url = scraper._get_next_page_url(url, 0)
        logger.info(f"Original: {url}")
        logger.info(f"Nächste:  {next_url}")
        logger.info("")
    
    scraper.close()


def test_detail_scraping():
    """Testet das Scrapen von Detail-Seiten."""
    from wg_scraper.models import WGListing
    
    logger.info("="*80)
    logger.info("Test: Detail-Scraping")
    logger.info("="*80)
    
    # Beispiel-URL (muss angepasst werden)
    url = input("Gib eine Detail-URL ein (oder Enter zum Überspringen): ").strip()
    
    if not url:
        logger.info("Übersprungen")
        return
    
    scraper = WGScraper(delay=1.5)
    
    try:
        listing = WGListing(
            listing_id="test",
            url=url,
            title="Test"
        )
        
        listing = scraper.scrape_listing_details(listing)
        
        logger.info(f"Titel: {listing.title}")
        logger.info(f"Beschreibung: {listing.description[:200]}..." if listing.description else "Keine Beschreibung")
        
    finally:
        scraper.close()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("WG-Scraper Test-Script")
    print("="*80)
    print("\nWähle einen Test:")
    print("1. Scraping testen (mit echter URL)")
    print("2. Pagination testen")
    print("3. Detail-Scraping testen")
    print("4. Alle Tests")
    print()
    
    choice = input("Auswahl (1-4): ").strip()
    
    if choice == "1":
        url = input("\nGib eine WG-Gesucht Such-URL ein: ").strip()
        if url:
            test_scraper(url, max_pages=2)
        else:
            logger.error("Keine URL angegeben")
    
    elif choice == "2":
        test_pagination()
    
    elif choice == "3":
        test_detail_scraping()
    
    elif choice == "4":
        test_pagination()
        print("\n")
        url = input("Gib eine WG-Gesucht Such-URL ein (oder Enter zum Überspringen): ").strip()
        if url:
            test_scraper(url, max_pages=1)
    
    else:
        logger.error("Ungültige Auswahl")
    
    print("\n" + "="*80)
    print("Test abgeschlossen")
    print("="*80 + "\n")
