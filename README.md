# WG-Gesucht Scraper

Genervt von wg-gesucht.de's suchinterface? Willst du eine tifere Analyse, oder einfach alle WGs mit offenen Stellen in einer Region? wg-scraper ist ein Python-CLI-Tool zum Scrapen von WG-Anzeigen von wg-gesucht.de und Lokaler Analyse der selbigen.

## Features

- 🔍 **Web Scraping**: Automatisches Scrapen von WG-Anzeigen
- 📄 **Pagination**: Iteriert automatisch durch alle Suchergebnis-Seiten
- 💾 **Datenbank**: SQLite-basierte lokale Datenspeicherung
- 📊 **Statistiken**: Analysiere gespeicherte Anzeigen
- 🎨 **CLI**: Benutzerfreundliche Kommandozeilen-Schnittstelle
- ⏱️ **Rate Limiting**: Konfigurierbare Verzögerung zwischen Requests

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- pip

### Setup

1. **Virtual Environment erstellen (falls noch nicht vorhanden):**
   ```bash
   python -m venv .env
   ```

2. **Virtual Environment aktivieren:**
   ```bash
   # Linux/Mac
   source .env/bin/activate
   
   # Windows
   .env\Scripts\activate
   ```

3. **Paket installieren:**
   ```bash
   pip install -e .
   ```

## Nutzung

### Grundlegende Befehle

#### 1. WG-Anzeigen scrapen

Gehe einfach wg-gesucht.de, gebe deine Filter ein und kopiere die gesamte URL. Der Scraper erledigt den Rest.

```bash
wg-scraper scrape "https://www.wg-gesucht.de/wg-zimmer-in-Berlin.8.0.1.0.html"
```

Mit optionalen Parametern:

```bash
wg-scraper scrape \
  --db-path meine_datenbank.db \
  --max-pages 5 \
  --delay 2.0 \
  "https://www.wg-gesucht.de/wg-zimmer-in-Berlin.8.0.1.0.html"
```

**Parameter:**
- `--db-path PATH`: Pfad zur SQLite-Datenbank (Standard: `wg_data.db`)
- `--max-pages INTEGER`: Maximale Anzahl zu scrapender Seiten (Standard: alle)
- `--delay FLOAT`: Verzögerung zwischen Requests in Sekunden (Standard: 1.0)

#### 2. Gespeicherte Anzeigen anzeigen

```bash
wg-scraper list
```

Mit Filtern:

```bash
wg-scraper list --limit 20 --city Berlin
```

**Parameter:**
- `--db-path PATH`: Pfad zur Datenbank
- `--limit INTEGER`: Anzahl anzuzeigender Anzeigen (Standard: 10)
- `--city TEXT`: Filter nach Stadt

#### 3. Statistiken anzeigen

```bash
wg-scraper stats
```

Zeigt an:
- Gesamtzahl der Anzeigen
- Anzahl unterschiedlicher Städte
- Durchschnittliche Miete
- Durchschnittliche Größe
- Top 5 Städte nach Anzahl

### Verbose-Modus

Für detaillierte Ausgaben verwende die `-v` Option:

```bash
# Info-Level
wg-scraper -v scrape "URL"

# Debug-Level
wg-scraper -vv scrape "URL"
```

## Projektstruktur

```
WG Scraper/
├── src/
│   └── wg_scraper/
│       ├── __init__.py      # Paket-Initialisierung
│       ├── cli.py           # CLI-Befehle (Click)
│       ├── scraper.py       # Web-Scraping-Logik
│       ├── database.py      # Datenbank-Verwaltung
│       ├── models.py        # Datenmodelle
│       └── skeleton.py      # PyScaffold-Beispiel (kann entfernt werden)
├── tests/                   # Unit-Tests
├── docs/                    # Dokumentation
├── setup.cfg               # Paket-Konfiguration
├── setup.py                # Setup-Script
└── README.md               # Diese Datei
```

## Datenbank-Schema

Die SQLite-Datenbank verwendet folgendes Schema:

**Tabelle: listings**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | INTEGER | Primärschlüssel (auto-increment) |
| listing_id | TEXT | Eindeutige ID von wg-gesucht.de |
| url | TEXT | URL zur Anzeige |
| title | TEXT | Titel der Anzeige |
| city | TEXT | Stadt |
| district | TEXT | Stadtteil/Bezirk |
| size | REAL | Größe in m² |
| rent | REAL | Miete in Euro (warm) |
| available_from | TEXT | Verfügbar ab |
| available_until | TEXT | Verfügbar bis |
| room_type | TEXT | Zimmerart |
| online_since | TEXT | Online seit |
| description | TEXT | Beschreibungstext |
| flatmates | INTEGER | Anzahl Mitbewohner |
| flatmate_details | TEXT | Details zu Mitbewohnern |
| features | TEXT | Ausstattungsmerkmale (komma-separiert) |
| images | TEXT | Bild-URLs (komma-separiert) |
| contact_name | TEXT | Ansprechpartner |
| scraped_at | TEXT | Zeitpunkt des Scrapings |
| created_at | TIMESTAMP | DB-Eintrag erstellt am |

## Entwicklung

### Tests ausführen

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=wg_scraper

# Spezifische Tests
pytest tests/test_skeleton.py
```

### Code-Style prüfen

```bash
# Flake8
flake8 src/

# Black (Formatting)
black src/ tests/
```

## Dependencies

- **click**: CLI-Framework
- **requests**: HTTP-Requests
- **beautifulsoup4**: HTML-Parsing
- **lxml**: XML/HTML-Parser (schneller als html.parser)

## Lizenz

MIT License - siehe [LICENSE.txt](LICENSE.txt)
## Beitragen

Contributions sind willkommen! Bitte erstelle ein Issue oder Pull Request.
