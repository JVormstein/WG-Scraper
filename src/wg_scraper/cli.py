"""
Command Line Interface für den WG-Gesucht Scraper.

Dieses Modul bietet die CLI-Funktionen zum Scrapen von WG-Gesucht.de
und zur Verwaltung der Datenbank.
"""

import logging
import sys
from pathlib import Path

import click

from wg_scraper import __version__
from wg_scraper.scraper import WGScraper
from wg_scraper.database import Database

__author__ = "Jonas"
__copyright__ = "Jonas"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


def setup_logging(loglevel):
    """Setup basic logging.

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel,
        stream=sys.stdout,
        format=logformat,
        datefmt="%Y-%m-%d %H:%M:%S"
    )


@click.group()
@click.version_option(version=__version__)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Erhöht die Ausgabe-Detailstufe (kann mehrfach angegeben werden).",
)
@click.pass_context
def main(ctx, verbose):
    """WG-Gesucht Scraper - Scrapt WG-Anzeigen und speichert sie in einer Datenbank."""
    # Logging-Level basierend auf Verbose-Count setzen
    loglevel = logging.WARNING
    if verbose == 1:
        loglevel = logging.INFO
    elif verbose >= 2:
        loglevel = logging.DEBUG
    
    setup_logging(loglevel)
    
    # Context-Objekt für Sub-Commands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@main.command()
@click.argument("url", type=str)
@click.option(
    "--db-path",
    type=click.Path(),
    default="wg_data.db",
    help="Pfad zur SQLite-Datenbank (Standard: wg_data.db).",
)
@click.option(
    "--max-pages",
    type=int,
    default=None,
    help="Maximale Anzahl der zu scrapenden Seiten (Standard: alle).",
)
@click.option(
    "--delay",
    type=float,
    default=1.0,
    help="Verzögerung zwischen Requests in Sekunden (Standard: 1.0).",
)
@click.pass_context
def scrape(ctx, url, db_path, max_pages, delay):
    """
    Scrapt WG-Anzeigen von der angegebenen URL.
    
    Die URL sollte eine Suchergebnis-Seite von wg-gesucht.de sein.
    Der Scraper iteriert automatisch durch alle Seiten der Suchergebnisse.
    
    Beispiel:
    
        wg-scraper scrape "https://www.wg-gesucht.de/wg-zimmer-in-Berlin.8.0.1.0.html"
    """
    _logger.info(f"Starte Scraping von: {url}")
    _logger.info(f"Datenbank: {db_path}")
    _logger.info(f"Max. Seiten: {max_pages if max_pages else 'Alle'}")
    _logger.info(f"Delay: {delay}s")
    
    try:
        # Datenbank initialisieren
        db = Database(db_path)
        db.init_db()
        _logger.info("Datenbank initialisiert")
        
        # Scraper initialisieren
        scraper = WGScraper(delay=delay)
        
        # Scraping durchführen
        results = scraper.scrape_search_results(url, max_pages=max_pages)
        
        # Ergebnisse in Datenbank speichern
        saved_count = 0
        for listing in results:
            if db.save_listing(listing):
                saved_count += 1
        
        _logger.info(f"Scraping abgeschlossen: {saved_count} neue Anzeigen gespeichert")
        click.echo(f"✓ {saved_count} neue WG-Anzeigen gespeichert in {db_path}")
        
    except Exception as e:
        _logger.error(f"Fehler beim Scraping: {e}", exc_info=True)
        click.echo(f"✗ Fehler: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="wg_data.db",
    help="Pfad zur SQLite-Datenbank.",
)
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Anzahl der anzuzeigenden Anzeigen (Standard: 10).",
)
@click.option(
    "--filter",
    "filter_str",
    type=str,
    default=None,
    help="Filter im Format 'field>value;field<value'. Bsp: 'size>20;rent<500;city=Berlin'",
)
@click.option(
    "--sort",
    type=str,
    default="scraped_at",
    help="Sortierung nach Feld (z.B. rent, size, scraped_at). Standard: scraped_at",
)
@click.option(
    "--order",
    type=click.Choice(['asc', 'desc'], case_sensitive=False),
    default="desc",
    help="Sortier-Reihenfolge: asc (aufsteigend) oder desc (absteigend). Standard: desc",
)
@click.pass_context
def list(ctx, db_path, limit, filter_str, sort, order):
    """
    Listet gespeicherte WG-Anzeigen aus der Datenbank auf.
    
    Verbosity-Level:
    - Standard: Zeigt wichtigste WG-Eigenschaften (Titel, Stadt, Miete, Größe, etc.)
    - -v: Zeigt zusätzlich alle WG-Details (Mitbewohner, Beschreibung, etc.)
    - -vv: Zeigt zusätzlich DB-Metadaten (DB-ID, Scraping-Zeitpunkt, etc.)
    
    Filter-Beispiele:
    
        --filter "size>20"                  # Größer als 20m²
        
        --filter "rent<500"                 # Miete unter 500€
        
        --filter "size>=20;rent<=600"       # Kombiniert
        
        --filter "city=Berlin"              # Exakte Stadt
    
    Sortierung:
    
        --sort rent --order asc             # Nach Miete aufsteigend
        
        --sort size --order desc            # Nach Größe absteigend
    """
    from wg_scraper.cli_utils import parse_filters
    
    verbose = ctx.obj.get('verbose', 0)
    
    try:
        db = Database(db_path)
        
        # Filter parsen
        filters = parse_filters(filter_str)
        
        # Listings abrufen
        listings = db.get_listings(
            limit=limit,
            filters=filters,
            sort_by=sort,
            sort_order=order.upper()
        )
        
        if not listings:
            click.echo("Keine Anzeigen gefunden.")
            return
        
        click.echo(f"\n{'='*80}")
        click.echo(f"Gefundene Anzeigen: {len(listings)}")
        if filter_str:
            click.echo(f"Filter: {filter_str}")
        click.echo(f"Sortierung: {sort} ({order})")
        click.echo(f"{'='*80}\n")
        
        for i, listing in enumerate(listings, 1):
            # Basis-Info (immer anzeigen)
            click.echo(f"{i}. {listing.get('title', 'N/A')}")
            click.echo(f"   Stadt: {listing.get('city', 'N/A')}", nl=False)
            if listing.get('district'):
                click.echo(f" ({listing['district']})")
            else:
                click.echo()
            
            click.echo(f"   Größe: {listing.get('size', 'N/A')} m² | Miete: {listing.get('rent', 'N/A')} €")
            click.echo(f"   Verfügbar ab: {listing.get('available_from', 'N/A')}")
            
            # Mit -v: Mehr Details
            if verbose >= 1:
                if listing.get('flatmates'):
                    click.echo(f"   WG-Größe: {listing['flatmates']}er WG", nl=False)
                    if listing.get('flatmate_details'):
                        click.echo(f" ({listing['flatmate_details']})")
                    else:
                        click.echo()
                
                if listing.get('room_type'):
                    click.echo(f"   Zimmerart: {listing['room_type']}")
                
                if listing.get('description'):
                    desc = listing['description']
                    if len(desc) > 150:
                        desc = desc[:150] + "..."
                    click.echo(f"   Beschreibung: {desc}")
            
            # Mit -vv: DB-Metadaten
            if verbose >= 2:
                click.echo(f"   DB-ID: {listing.get('id', 'N/A')}")
                click.echo(f"   Listing-ID: {listing.get('listing_id', 'N/A')}")
                click.echo(f"   Gescrapt am: {listing.get('scraped_at', 'N/A')}")
                click.echo(f"   Erstellt am: {listing.get('created_at', 'N/A')}")
            
            click.echo(f"   URL: {listing.get('url', 'N/A')}")
            click.echo(f"{'-'*80}\n")
            
    except Exception as e:
        _logger.error(f"Fehler beim Abrufen der Daten: {e}", exc_info=True)
        click.echo(f"✗ Fehler: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="wg_data.db",
    help="Pfad zur SQLite-Datenbank.",
)
def stats(db_path):
    """
    Zeigt Statistiken über die gespeicherten Anzeigen an.
    """
    try:
        db = Database(db_path)
        statistics = db.get_statistics()
        
        click.echo(f"\n{'='*80}")
        click.echo("Datenbank-Statistiken")
        click.echo(f"{'='*80}\n")
        click.echo(f"Gesamt Anzeigen: {statistics.get('total', 0)}")
        click.echo(f"Städte: {statistics.get('cities', 0)}")
        click.echo(f"Durchschn. Miete: {statistics.get('avg_rent', 0):.2f} €")
        click.echo(f"Durchschn. Größe: {statistics.get('avg_size', 0):.2f} m²")
        click.echo(f"\nTop 5 Städte:")
        for city, count in statistics.get('top_cities', []):
            click.echo(f"  - {city}: {count} Anzeigen")
        click.echo()
        
    except Exception as e:
        _logger.error(f"Fehler beim Abrufen der Statistiken: {e}", exc_info=True)
        click.echo(f"✗ Fehler: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("destination", type=str)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="wg_data.db",
    help="Pfad zur SQLite-Datenbank.",
)
@click.option(
    "--mode",
    type=click.Choice(['driving', 'car', 'transit', 'cycling', 'bike', 'walking', 'foot'], case_sensitive=False),
    default="driving",
    help="Verkehrsmittel: driving/car (Auto), cycling/bike (Fahrrad), walking/foot (zu Fuß). Standard: driving",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Anzahl der zu analysierenden Anzeigen (Standard: 20).",
)
@click.option(
    "--filter",
    "filter_str",
    type=str,
    default=None,
    help="Filter wie bei 'list' Command (z.B. 'rent<500;size>20')",
)
@click.option(
    "--sort-by-distance",
    is_flag=True,
    help="Sortiere Ergebnisse nach Distanz (Standard: nach DB-Reihenfolge)",
)
def route(destination, db_path, mode, limit, filter_str, sort_by_distance):
    """
    Berechnet Routen und Distanzen zu einem Zielort.
    
    Zeigt für jede WG-Anzeige:
    - Luftlinie zum Ziel
    - Fahrstrecke (wenn verfügbar)
    - Fahrzeit (wenn verfügbar)
    
    DESTINATION: Zieladresse (z.B. "Hauptbahnhof Stuttgart" oder "Universitätsstraße 1, Berlin")
    
    Beispiele:
    
        wg-scraper route "Marienplatz München"
        
        wg-scraper route "Hauptbahnhof Stuttgart" --mode cycling
        
        wg-scraper route "TU Berlin" --filter "rent<600" --limit 10
        
        wg-scraper route "Alexanderplatz" --sort-by-distance
    """
    from wg_scraper.cli_utils import parse_filters, geocode_address, calculate_route
    
    try:
        # Ziel geocoden
        click.echo(f"Geocodiere Ziel: {destination}...")
        dest_coords = geocode_address(destination)
        
        if not dest_coords:
            click.echo(f"✗ Konnte Zieladresse nicht finden: {destination}", err=True)
            sys.exit(1)
        
        click.echo(f"✓ Ziel gefunden: {dest_coords[0]:.4f}, {dest_coords[1]:.4f}\n")
        
        # Listings abrufen
        db = Database(db_path)
        filters = parse_filters(filter_str)
        listings = db.get_listings(limit=limit, filters=filters)
        
        if not listings:
            click.echo("Keine Anzeigen gefunden.")
            return
        
        click.echo(f"Berechne Routen für {len(listings)} Anzeigen...")
        click.echo(f"Verkehrsmittel: {mode}")
        click.echo()
        
        # Routen berechnen
        results = []
        
        with click.progressbar(listings, label='Berechnung') as bar:
            for listing in bar:
                # Adresse zusammenbauen
                address_parts = []
                if listing.get('city'):
                    address_parts.append(listing['city'])
                if listing.get('district'):
                    address_parts.append(listing['district'])
                
                if not address_parts:
                    continue
                
                address = ", ".join(address_parts)
                
                # Geocoden
                coords = geocode_address(address)
                if not coords:
                    continue
                
                # Route berechnen
                route_info = calculate_route(coords, dest_coords, mode)
                
                if route_info:
                    results.append({
                        'listing': listing,
                        'route': route_info
                    })
        
        if not results:
            click.echo("\n✗ Keine Routen berechnet.")
            return
        
        # Optional sortieren
        if sort_by_distance:
            results.sort(key=lambda x: x['route']['straight_line_km'])
        
        # Ausgabe
        click.echo(f"\n{'='*80}")
        click.echo(f"Routen zum Ziel: {destination}")
        click.echo(f"{'='*80}\n")
        
        for i, result in enumerate(results, 1):
            listing = result['listing']
            route = result['route']
            
            click.echo(f"{i}. {listing.get('title', 'N/A')}")
            click.echo(f"   {listing.get('city', 'N/A')}", nl=False)
            if listing.get('district'):
                click.echo(f" - {listing['district']}")
            else:
                click.echo()
            
            click.echo(f"   Miete: {listing.get('rent', 'N/A')} € | Größe: {listing.get('size', 'N/A')} m²")
            
            # Distanzen
            click.echo(f"   Luftlinie: {route['straight_line_km']} km", nl=False)
            
            if route['distance_km']:
                click.echo(f" | {mode.title()}: {route['distance_km']} km", nl=False)
            
            if route['duration_min']:
                click.echo(f" (~{route['duration_min']} min)")
            else:
                click.echo()
            
            click.echo(f"   URL: {listing.get('url', 'N/A')}")
            click.echo(f"{'-'*80}\n")
        
    except KeyboardInterrupt:
        click.echo("\n\nAbgebrochen durch Benutzer")
        sys.exit(0)
    except Exception as e:
        _logger.error(f"Fehler bei Routen-Berechnung: {e}", exc_info=True)
        click.echo(f"✗ Fehler: {e}", err=True)
        sys.exit(1)


def run():
    """Entry point für die console_scripts."""
    main(obj={})


if __name__ == "__main__":
    run()
