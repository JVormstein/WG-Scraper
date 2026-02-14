"""
Command Line Interface für den WG-Gesucht Scraper.

Dieses Modul bietet die CLI-Funktionen zum Scrapen von WG-Gesucht.de
und zur Verwaltung der Datenbank.
"""

import logging
import sys
from pathlib import Path
from typing import Any

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
    "--metrics",
    "metrics_str",
    type=str,
    default=None,
    help=(
        "Analyse-Funktionen (Komma-separiert), z.B. "
        "'route,ppm,avg_ppm_diff,ms_diff'"
    ),
)
@click.option(
    "--rent-index",
    type=float,
    default=None,
    help="Mietspiegel in EUR/m² (nur fuer ms_diff).",
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
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Exportiere Ergebnisse in Datei (Format: .txt, .csv, .json). Bsp: --output results.csv",
)
@click.option(
    "--addr",
    type=str,
    default=None,
    help="Zieladresse fuer Routing-Analyse (nur mit --metrics route).",
)
@click.option(
    "--route-mode",
    type=click.Choice(['driving', 'car', 'transit', 'cycling', 'bike', 'walking', 'foot'], case_sensitive=False),
    default="driving",
    help="Verkehrsmittel fuer Routing: driving/car (Auto), cycling/bike (Fahrrad), walking/foot (zu Fuss). Standard: driving",
)
@click.option(
    "--sort-by-distance",
    is_flag=True,
    help="Sortiere Ergebnisse nach Distanz (nur mit --addr).",
)
@click.pass_context
def list(
    ctx,
    db_path,
    limit,
    filter_str,
    metrics_str,
    rent_index,
    sort,
    order,
    output,
    addr,
    route_mode,
    sort_by_distance,
):
    """
    Listet gespeicherte WG-Anzeigen aus der Datenbank auf.
    
    Verbosity-Level:
    - Standard: Zeigt wichtigste WG-Eigenschaften (Titel, Stadt, Miete, Größe, etc.)
    - -v: Zeigt zusätzlich alle WG-Details (Mitbewohner, Beschreibung, etc.)
    - -vv: Zeigt zusätzlich DB-Metadaten (DB-ID, Scraping-Zeitpunkt, etc.)

    Analyse (optional):
    - Aktivierung ueber --metrics (z.B. route,ppm,avg_ppm_diff,ms_diff).
    - route benoetigt --addr; --route-mode bestimmt das Verkehrsmittel.
    - --sort-by-distance sortiert nach Luftlinie (nur mit route).
    - ms_diff benoetigt --rent-index (EUR/m²).
    
    Filter-Beispiele:
    
        --filter "size>20"                  # Größer als 20m²
        
        --filter "rent<500"                 # Miete unter 500€
        
        --filter "size>=20;rent<=600"       # Kombiniert
        
        --filter "city=Berlin"              # Exakte Stadt
    
    Sortierung:
    
        --sort rent --order asc             # Nach Miete aufsteigend
        
        --sort size --order desc            # Nach Größe absteigend
        
        --sort ppm --order asc               # Nach Preis pro m²
        
        --sort straight_line_km --order asc  # Nach Distanz (mit route)
    """
    from wg_scraper.cli_utils import (
        parse_filters,
        geocode_address,
        calculate_route,
        export_listings,
        export_routes,
    )
    
    verbose = ctx.obj.get('verbose', 0)
    
    try:
        db = Database(db_path)

        metric_aliases = {
            'ppm': 'price_per_sqm',
            'price_per_sqm': 'price_per_sqm',
            'avg_ppm_diff': 'avg_ppm_diff',
            'avg_qm_diff': 'avg_ppm_diff',
            'ms_diff': 'rent_index_diff',
            'mietspiegel_diff': 'rent_index_diff',
            'rent_index_diff': 'rent_index_diff',
            'distance_km': 'distance_km',
            'duration_min': 'duration_min',
            'straight_line_km': 'straight_line_km',
            'route': 'route'
        }

        def normalize_metric(name: str) -> str:
            return metric_aliases.get(name.lower(), name)

        def split_filter_key(key: str) -> tuple:
            for op in ('>=', '<=', '!=', '>', '<'):
                if key.endswith(op):
                    return key[:-len(op)], op
            return key, '='

        def to_key(field: str, op: str) -> str:
            return field if op == '=' else f"{field}{op}"

        def passes_filter(value: Any, op: str, expected: Any) -> bool:
            if value is None:
                return False
            try:
                if op == '=':
                    return value == expected
                if op == '!=':
                    return value != expected
                if op == '>':
                    return value > expected
                if op == '<':
                    return value < expected
                if op == '>=':
                    return value >= expected
                if op == '<=':
                    return value <= expected
            except TypeError:
                return False
            return False

        def apply_metric_filters(items, metric_filters, use_results: bool):
            if not metric_filters:
                return items
            filtered_items = []
            for item in items:
                listing = item['listing'] if use_results else item
                matched = True
                for key, expected in metric_filters.items():
                    base, op = split_filter_key(key)
                    value = listing.get(base)
                    if not passes_filter(value, op, expected):
                        matched = False
                        break
                if matched:
                    filtered_items.append(item)
            return filtered_items

        metrics = set()
        if metrics_str:
            for part in metrics_str.split(','):
                part = part.strip()
                if part:
                    metrics.add(normalize_metric(part))

        route_fields = {'straight_line_km', 'distance_km', 'duration_min'}
        metric_fields = {'price_per_sqm', 'avg_ppm_diff', 'rent_index_diff'} | route_fields

        filters = parse_filters(filter_str)
        db_filters = {}
        metric_filters = {}

        for key, value in filters.items():
            base, op = split_filter_key(key)
            normalized = normalize_metric(base)
            if normalized in metric_fields:
                metric_filters[to_key(normalized, op)] = value
            else:
                db_filters[key] = value

        sort_field = normalize_metric(sort)
        sort_in_memory = sort_field in metric_fields

        if sort_by_distance:
            sort_field = 'straight_line_km'
            sort_in_memory = True

        metrics_needed = set(metrics)
        metrics_needed.update({split_filter_key(k)[0] for k in metric_filters.keys()})
        if sort_in_memory and sort_field in metric_fields:
            metrics_needed.add(sort_field)

        route_requested = 'route' in metrics_needed or any(field in route_fields for field in metrics_needed)

        # Listings abrufen
        listings = db.get_listings(
            limit=limit,
            filters=db_filters,
            sort_by=None if sort_in_memory else sort,
            sort_order=order.upper()
        )

        if not listings:
            click.echo("Keine Anzeigen gefunden.")
            return

        # Preis pro Quadratmeter berechnen
        if any(metric in metrics_needed for metric in ['price_per_sqm', 'avg_ppm_diff', 'rent_index_diff']):
            for listing in listings:
                rent = listing.get('rent')
                size = listing.get('size')
                if rent is not None and size:
                    listing['price_per_sqm'] = round(rent / size, 2)
                else:
                    listing['price_per_sqm'] = None

        if 'avg_ppm_diff' in metrics_needed:
            ppm_values = [l.get('price_per_sqm') for l in listings if l.get('price_per_sqm') is not None]
            avg_ppm = round(sum(ppm_values) / len(ppm_values), 2) if ppm_values else None
            for listing in listings:
                if listing.get('price_per_sqm') is None or avg_ppm is None:
                    listing['avg_ppm_diff'] = None
                else:
                    listing['avg_ppm_diff'] = round(listing['price_per_sqm'] - avg_ppm, 2)

        if 'rent_index_diff' in metrics_needed:
            if rent_index is None:
                click.echo("⚠ Kein Mietspiegel angegeben. Verwende --rent-index EUR/qm.")
            for listing in listings:
                if listing.get('price_per_sqm') is None or rent_index is None:
                    listing['rent_index_diff'] = None
                else:
                    listing['rent_index_diff'] = round(listing['price_per_sqm'] - rent_index, 2)

        results = None
        if route_requested:
            if not addr:
                click.echo("✗ --addr ist erforderlich fuer Routing-Analyse.", err=True)
                sys.exit(1)

            click.echo(f"Geocodiere Ziel: {addr}...")
            dest_coords = geocode_address(addr)

            if not dest_coords:
                click.echo(f"✗ Konnte Zieladresse nicht finden: {addr}", err=True)
                sys.exit(1)

            click.echo(f"✓ Ziel gefunden: {dest_coords[0]:.4f}, {dest_coords[1]:.4f}\n")

            click.echo(f"Berechne Routen fuer {len(listings)} Anzeigen...")
            click.echo(f"Verkehrsmittel: {route_mode}")
            click.echo()

            results = []

            with click.progressbar(listings, label='Berechnung') as bar:
                for listing in bar:
                    address_parts = []
                    if listing.get('city'):
                        address_parts.append(listing['city'])
                    if listing.get('district'):
                        address_parts.append(listing['district'])

                    if not address_parts:
                        continue

                    address = ", ".join(address_parts)

                    coords = geocode_address(address)
                    if not coords:
                        continue

                    route_info = calculate_route(coords, dest_coords, route_mode)

                    if route_info:
                        listing.update(route_info)
                        results.append({
                            'listing': listing,
                            'route': route_info
                        })

            if not results:
                click.echo("\n✗ Keine Routen berechnet.")
                return

            results = apply_metric_filters(results, metric_filters, use_results=True)
            listings = [item['listing'] for item in results]

            if sort_in_memory:
                reverse = order.lower() == 'desc'
                results.sort(
                    key=lambda x: (x['listing'].get(sort_field) is None, x['listing'].get(sort_field)),
                    reverse=reverse
                )
        else:
            listings = apply_metric_filters(listings, metric_filters, use_results=False)

            if sort_in_memory:
                reverse = order.lower() == 'desc'
                listings.sort(
                    key=lambda x: (x.get(sort_field) is None, x.get(sort_field)),
                    reverse=reverse
                )

        if not listings:
            click.echo("Keine Anzeigen gefunden.")
            return

        header_title = f"Routen zum Ziel: {addr}" if route_requested else "Gefundene Anzeigen"
        click.echo(f"\n{'='*80}")
        click.echo(header_title)
        click.echo(f"Anzahl Ergebnisse: {len(listings)}")
        if filter_str:
            click.echo(f"Filter: {filter_str}")
        if metrics_str:
            click.echo(f"Analyse: {metrics_str}")
        if not route_requested:
            click.echo(f"Sortierung: {sort} ({order})")
        click.echo(f"{'='*80}\n")

        for i, listing in enumerate(listings, 1):
            click.echo(f"{i}. {listing.get('title', 'N/A')}")
            click.echo(f"   Stadt: {listing.get('city', 'N/A')}", nl=False)
            if listing.get('district'):
                click.echo(f" ({listing['district']})")
            else:
                click.echo()

            click.echo(f"   Größe: {listing.get('size', 'N/A')} m² | Miete: {listing.get('rent', 'N/A')} €")
            click.echo(f"   Verfügbar ab: {listing.get('available_from', 'N/A')}")

            if listing.get('price_per_sqm') is not None:
                click.echo(f"   Preis pro m2: {listing.get('price_per_sqm')} €", nl=False)
                if listing.get('avg_ppm_diff') is not None:
                    click.echo(f" | Delta avg/m2: {listing.get('avg_ppm_diff')} €", nl=False)
                if listing.get('rent_index_diff') is not None:
                    click.echo(f" | Delta Mietspiegel: {listing.get('rent_index_diff')} €", nl=False)
                click.echo()

            if route_requested:
                click.echo(f"   Luftlinie: {listing.get('straight_line_km', 'N/A')} km", nl=False)
                if listing.get('distance_km'):
                    click.echo(f" | {route_mode.title()}: {listing.get('distance_km')} km", nl=False)
                if listing.get('duration_min'):
                    click.echo(f" (~{listing.get('duration_min')} min)")
                else:
                    click.echo()

            if verbose >= 1:
                if listing.get('available_until'):
                    click.echo(f"   Verfügbar bis: {listing['available_until']}")

                if listing.get('flatmates'):
                    flatmate_line = f"   WG-Größe: {listing['flatmates']}er WG"
                    details = []
                    if listing.get('flatmates_female') is not None:
                        details.append(f"{listing['flatmates_female']}w")
                    if listing.get('flatmates_male') is not None:
                        details.append(f"{listing['flatmates_male']}m")
                    if listing.get('flatmates_diverse') is not None:
                        details.append(f"{listing['flatmates_diverse']}d")
                    if listing.get('rooms_free') is not None:
                        details.append(f"{listing['rooms_free']} frei")
                    if listing.get('flatmate_details') and not details:
                        details.append(listing['flatmate_details'])
                    if details:
                        flatmate_line += f" ({', '.join(details)})"
                    click.echo(flatmate_line)

                if listing.get('room_type'):
                    click.echo(f"   Zimmerart: {listing['room_type']}")

                if listing.get('online_since'):
                    click.echo(f"   Online seit: {listing['online_since']}")

            if verbose >= 2:
                if listing.get('description'):
                    desc = listing['description']
                    if len(desc) > 200:
                        desc = desc[:200] + "..."
                    click.echo(f"   Beschreibung: {desc}")

                if listing.get('features'):
                    click.echo(f"   Features: {listing['features']}")

                if listing.get('contact_name'):
                    click.echo(f"   Kontakt: {listing['contact_name']}")

                click.echo(f"   DB-ID: {listing.get('id', 'N/A')} | Listing-ID: {listing.get('listing_id', 'N/A')}")
                click.echo(f"   Gescrapt am: {listing.get('scraped_at', 'N/A')}")
                if listing.get('created_at'):
                    click.echo(f"   Erstellt am: {listing.get('created_at')}")

            click.echo(f"   URL: {listing.get('url', 'N/A')}")
            click.echo(f"{'-'*80}\n")

        if output:
            if route_requested and results is not None:
                if export_routes(results, output, addr, route_mode, verbose=verbose):
                    click.echo(f"\n✓ {len(listings)} Routen exportiert nach: {output}")
                else:
                    click.echo(f"\n✗ Export fehlgeschlagen", err=True)
            else:
                if export_listings(listings, output, verbose=verbose):
                    click.echo(f"\n✓ {len(listings)} Anzeigen exportiert nach: {output}")
                else:
                    click.echo(f"\n✗ Export fehlgeschlagen", err=True)
            
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
