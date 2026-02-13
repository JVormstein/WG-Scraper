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
    "--city",
    type=str,
    default=None,
    help="Filtere nach Stadt.",
)
def list(db_path, limit, city):
    """
    Listet gespeicherte WG-Anzeigen aus der Datenbank auf.
    """
    try:
        db = Database(db_path)
        listings = db.get_listings(limit=limit, city=city)
        
        if not listings:
            click.echo("Keine Anzeigen gefunden.")
            return
        
        click.echo(f"\n{'='*80}")
        click.echo(f"Gefundene Anzeigen: {len(listings)}")
        click.echo(f"{'='*80}\n")
        
        for listing in listings:
            click.echo(f"ID: {listing.get('id', 'N/A')}")
            click.echo(f"Titel: {listing.get('title', 'N/A')}")
            click.echo(f"Stadt: {listing.get('city', 'N/A')}")
            click.echo(f"Größe: {listing.get('size', 'N/A')} m²")
            click.echo(f"Miete: {listing.get('rent', 'N/A')} €")
            click.echo(f"Verfügbar ab: {listing.get('available_from', 'N/A')}")
            click.echo(f"URL: {listing.get('url', 'N/A')}")
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


def run():
    """Entry point für die console_scripts."""
    main(obj={})


if __name__ == "__main__":
    run()
