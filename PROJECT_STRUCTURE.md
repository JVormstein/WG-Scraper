# WG-Scraper - Projektstruktur

## 📁 Übersicht

```
WG Scraper/
│
├── 📝 Dokumentation
│   ├── README_USAGE.md          # Vollständige Bedienungsanleitung
│   ├── QUICKSTART.md            # Schnellstart-Guide
│   ├── README.rst               # PyScaffold Standard-README
│   ├── AUTHORS.rst              # Autoren
│   ├── CHANGELOG.rst            # Änderungsprotokoll
│   ├── CONTRIBUTING.rst         # Beiträge-Richtlinien
│   └── LICENSE.txt              # MIT-Lizenz
│
├── 💻 Quellcode (src/wg_scraper/)
│   ├── __init__.py              # Paket-Initialisierung & Versionierung
│   ├── cli.py                   # ✅ CLI-Befehle (Click)
│   ├── scraper.py               # ⏳ Web-Scraping-Logik (TODO)
│   ├── database.py              # ✅ SQLite-Datenbank-Verwaltung
│   ├── models.py                # ✅ Datenmodelle (WGListing)
│   ├── config.py                # ✅ Konfiguration & Konstanten
│   └── skeleton.py              # PyScaffold-Beispiel (kann entfernt werden)
│
├── 🧪 Tests
│   ├── conftest.py              # Pytest-Konfiguration
│   └── test_skeleton.py         # Beispiel-Tests
│
├── 📚 Beispiele & Hilfsmittel
│   ├── examples.py              # ✅ Beispiel-Script für API-Nutzung
│   └── requirements-dev.txt     # ✅ Development-Dependencies
│
├── ⚙️ Konfiguration
│   ├── setup.cfg                # ✅ Package-Konfiguration (aktualisiert)
│   ├── setup.py                 # Setup-Script
│   ├── pyproject.toml           # Build-System-Konfiguration
│   ├── tox.ini                  # Tox-Test-Umgebungen
│   └── .gitignore               # ✅ Git-Ignore (mit DB-Dateien)
│
├── 📦 Installation
│   └── .env/                    # Virtual Environment
│
└── 🗄️ Daten (wird erstellt)
    ├── wg_data.db               # Produktions-Datenbank
    └── example_data.db          # Test-Datenbank

Legende:
✅ = Implementiert und getestet
⏳ = Grundstruktur vorhanden, muss angepasst werden
```

## 🎯 Kernmodule

### 1. CLI (cli.py) ✅

**Funktionalität:**
- `scrape`: WG-Anzeigen von URL scrapen
- `list`: Gespeicherte Anzeigen anzeigen
- `stats`: Statistiken über Anzeigen

**Status:** Vollständig implementiert

**Nutzung:**
```bash
.env/bin/wg-scraper scrape "URL"
.env/bin/wg-scraper list --city Berlin
.env/bin/wg-scraper stats
```

---

### 2. Scraper (scraper.py) ⏳

**Funktionalität:**
- `WGScraper`: Hauptklasse für Web-Scraping
- `scrape_search_results()`: Iteriert durch Suchergebnisse
- `scrape_listing_details()`: Detail-Seiten scrapen (optional)

**Status:** Grundstruktur mit Platzhaltern

**TODOs:**
- [ ] HTML-Selektoren anpassen
- [ ] Listing-Parsing implementieren
- [ ] Pagination implementieren
- [ ] ID-Extraktion anpassen

**Wichtige Methoden:**
```python
scraper = WGScraper(delay=1.0)
for listing in scraper.scrape_search_results(url, max_pages=5):
    print(listing)
```

---

### 3. Database (database.py) ✅

**Funktionalität:**
- SQLite-Datenbank-Verwaltung
- CRUD-Operationen für Listings
- Statistiken und Filterung

**Status:** Vollständig implementiert

**API:**
```python
db = Database("wg_data.db")
db.init_db()
db.save_listing(listing)
listings = db.get_listings(city="Berlin", max_rent=500)
stats = db.get_statistics()
```

---

### 4. Models (models.py) ✅

**Funktionalität:**
- `WGListing`: Dataclass für WG-Anzeigen
- Serialisierung (to_dict/from_dict)

**Status:** Vollständig implementiert

**Felder:**
- `listing_id`, `url`, `title` (Pflicht)
- `city`, `size`, `rent`, `available_from` (Optional)
- Viele weitere optionale Felder

---

### 5. Config (config.py) ✅

**Funktionalität:**
- Zentrale Konfiguration
- CSS-Selektoren (müssen angepasst werden!)
- Umgebungsvariablen-Support

**Status:** Grundstruktur vorhanden

**TODOs:**
- [ ] CSS-Selektoren an wg-gesucht.de anpassen

---

## 🗄️ Datenbank-Schema

### Tabelle: listings

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INTEGER | Auto-increment PK |
| listing_id | TEXT | Eindeutige ID (unique) |
| url | TEXT | URL zur Anzeige |
| title | TEXT | Titel |
| city | TEXT | Stadt |
| size | REAL | Größe in m² |
| rent | REAL | Miete in € |
| ... | ... | (weitere Felder siehe models.py) |

**Indizes:**
- `idx_city` auf `city`
- `idx_rent` auf `rent`
- `idx_scraped_at` auf `scraped_at`

---

## 🔄 Workflow

### Entwicklung

```bash
# 1. Scraper anpassen
code src/wg_scraper/scraper.py

# 2. Selektoren in Config eintragen
code src/wg_scraper/config.py

# 3. Mit 1 Seite testen
.env/bin/wg-scraper -vv scrape --max-pages 1 "URL"

# 4. Tests schreiben
code tests/test_scraper.py
.env/bin/pytest

# 5. Produktiv nutzen
.env/bin/wg-scraper scrape "URL"
```

### Produktive Nutzung

```bash
# Scrapen
.env/bin/wg-scraper scrape "URL" --delay 2.0

# Auswerten
.env/bin/wg-scraper list --city Berlin
.env/bin/wg-scraper stats

# Backup
cp wg_data.db wg_data_backup_$(date +%Y%m%d).db
```

---

## 🧩 Dependencies

### Produktiv (install_requires)
- **click** ≥ 8.0: CLI-Framework
- **requests** ≥ 2.28.0: HTTP-Client
- **beautifulsoup4** ≥ 4.11.0: HTML-Parser
- **lxml** ≥ 4.9.0: XML/HTML-Parser

### Development (requirements-dev.txt)
- **pytest**: Testing
- **flake8**: Linting
- **black**: Code-Formatting
- **mypy**: Type-Checking

---

## 📊 Entry Points

Konfiguriert in `setup.cfg`:

```ini
[options.entry_points]
console_scripts =
    wg-scraper = wg_scraper.cli:run
```

Nach Installation verfügbar als:
```bash
wg-scraper  # (im aktivierten venv)
.env/bin/wg-scraper  # (direkter Pfad)
```

---

## 🎓 Beispiel-Nutzung

### Via CLI
```bash
# Scrapen
.env/bin/wg-scraper scrape "https://www.wg-gesucht.de/..."

# Anzeigen
.env/bin/wg-scraper list

# Mit Filter
.env/bin/wg-scraper list --city München --limit 20
```

### Via Python API
```python
from wg_scraper.scraper import WGScraper
from wg_scraper.database import Database

# Scrapen
scraper = WGScraper(delay=1.5)
listings = scraper.scrape_search_results(url, max_pages=3)

# Speichern
db = Database()
db.init_db()
for listing in listings:
    db.save_listing(listing)

# Abfragen
berlin_listings = db.get_listings(city="Berlin", max_rent=500)
```

Siehe [examples.py](examples.py) für vollständige Beispiele.

---

## 📝 Nächste Schritte

### Priorität 1: Scraping implementieren
1. wg-gesucht.de im Browser analysieren
2. CSS-Selektoren identifizieren
3. `scraper.py` anpassen
4. Testen mit `--max-pages 1`

### Priorität 2: Tests
1. Test-Cases schreiben
2. Mock-Responses nutzen
3. Edge-Cases abdecken

### Priorität 3: Features
1. Export-Funktion (CSV, JSON)
2. Mehr Filter-Optionen
3. Benachrichtigungen bei neuen Anzeigen
4. Web-Interface (Flask/Streamlit)

---

## 🔗 Wichtige Dateien zum Starten

1. **[QUICKSTART.md](QUICKSTART.md)** - Schnellstart-Guide
2. **[README_USAGE.md](README_USAGE.md)** - Vollständige Dokumentation
3. **[examples.py](examples.py)** - Code-Beispiele
4. **[src/wg_scraper/scraper.py](src/wg_scraper/scraper.py)** - Hier wird implementiert!

---

**Projekt-Status:** 🟢 Grundstruktur fertig | 🟡 Scraping-Implementierung ausstehend

*Erstellt: 13. Februar 2026*
