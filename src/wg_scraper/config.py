"""
Konfigurationsdatei für den WG-Gesucht Scraper.

Zentrale Einstellungen und Konstanten.
"""

import os
from pathlib import Path

# Basis-URL von wg-gesucht.de
BASE_URL = "https://www.wg-gesucht.de"

# Default-Verzögerung zwischen Requests (in Sekunden)
DEFAULT_DELAY = 1.0

# Standard-Pfad für die Datenbank
DEFAULT_DB_PATH = "wg_data.db"

# User-Agent für HTTP-Requests
# Ein realistischer User-Agent hilft, nicht als Bot erkannt zu werden
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Request-Timeout in Sekunden
REQUEST_TIMEOUT = 30

# Maximale Anzahl Retry-Versuche bei fehlgeschlagenen Requests
MAX_RETRIES = 3

# Logging-Konfiguration
LOG_FORMAT = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# CSS-Selektoren für das Scraping
# Diese müssen an die tatsächliche Struktur der Website angepasst werden!
#
# SYNTAX-REGELN:
# - Punkt (.) für CSS-Klassen: "div.class-name"
# - Leerzeichen für Nachfahren: "div.parent a" (a irgendwo in div)
# - > für direkte Kinder: "div > a" (a direkt unter div)
# - Kein Punkt vor HTML-Tags: "div a" nicht "div.a"
# - Attribute in []: "a[href]" oder "img[src]"
#
# WICHTIG: Alle "listing_*" Selektoren werden RELATIV zum "listing_container" gesucht!
# D.h. zuerst werden alle Container gefunden, dann in jedem Container die Details.
SELECTORS = {
    # Suchergebnisse - Hauptcontainer
    "listing_container": "div.offer_list_item",  # Container für einzelne Anzeigen (auf Suchseite)
    
    # Details innerhalb eines Containers (relativ zum listing_container)
    "listing_link": "h2.truncate_title a[href]",  # Link zur Detailseite (z.B. in h3 oder direktes a-Tag)
    "listing_title": "h2.truncate_title > a",  # Titel der Anzeige
    "listing_neighbors" : "div.col-xs-11 span:nth-of-type(2)", # Anzahl und Geschlecht der Mitbewohner, sowie gesamte WG Größe
                                                               # In der Form `Xer WG (Yw,Ym,Yd,Yn)` !Steht im Tetel des Span, nicht im Inhalt!
    
    "listing_size": "div.row div.col-sm-8 div:nth-of-type(2) div:nth-of-type(3) b",  # Größe (z.B. "20 m²")
    "listing_rent": "div.row div.col-sm-8 div:nth-of-type(2) div:nth-of-type(1) b",  # Miete (z.B. "450 €")
    "listing_address": "div.col-xs-11 span:nth-of-type(1)", # In der Form `(Uninteressant) | Stadt/Stadteil | Straße & Hausnummer`
    "listing_available": "div.row div.col-sm-8 div:nth-of-type(2) div:nth-of-type(2)",  # Verfügbarkeit (z.B. "01.03.2026")
    
    # Detailseite (optional) - hier wird auf der ganzen Seite gesucht
    "detail_description": "div.freitext_0 p",  # Beschreibungstext
    "detail_desc_location": "div.freitext_1 p",  # Beschreibungstext
    "detail_desc_social": "div.freitext_2 p",  # Beschreibungstext
    "detail_desc_other": "div.freitext_3 p",  # Beschreibungstext
}

# Datenbank-Einstellungen
DB_CONFIG = {
    "check_same_thread": False,  # Erlaubt Multi-Threading (Vorsicht!)
    "timeout": 10.0,  # Timeout für Datenbank-Locks
}

# Umgebungsvariablen-Support
# Diese können über OS-Umgebungsvariablen überschrieben werden

def get_config(key: str, default=None):
    """
    Holt einen Konfigurationswert, prüft zuerst Umgebungsvariablen.
    
    Args:
        key: Konfigurations-Schlüssel (z.B. "WG_SCRAPER_DELAY")
        default: Standard-Wert wenn nicht gesetzt
        
    Returns:
        Konfigurationswert
    """
    env_key = f"WG_SCRAPER_{key.upper()}"
    return os.getenv(env_key, default)


# Zu verwendende Werte (können über Env-Vars überschrieben werden)
DELAY = float(get_config("delay", DEFAULT_DELAY))
DB_PATH = get_config("db_path", DEFAULT_DB_PATH)

# Workspace-Pfad
WORKSPACE_DIR = Path(__file__).parent.parent.parent
