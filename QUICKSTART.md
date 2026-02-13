# WG-Scraper - Quick Start Guide

## 🚀 Schnellstart

### 1. Installation überprüfen

Das Projekt ist bereits installiert. Teste es mit:

```bash
.env/bin/wg-scraper --version
```

### 2. Erste Schritte

#### Hilfe anzeigen
```bash
.env/bin/wg-scraper --help
```

#### Beispiel-Daten testen
Das Projekt enthält Beispiel-Daten zum Testen:

```bash
# Beispiel-Script ausführen (erstellt example_data.db)
.env/bin/python examples.py

# Listings anzeigen
.env/bin/wg-scraper list --db-path example_data.db

# Statistiken anzeigen
.env/bin/wg-scraper stats --db-path example_data.db
```

### 3. Eigenes Scraping (nach Implementierung)

**⚠️ WICHTIG**: Die Scraping-Funktionalität muss noch implementiert werden!

Siehe: [src/wg_scraper/scraper.py](src/wg_scraper/scraper.py)

Nach der Implementierung:

```bash
# WG-Anzeigen scrapen
.env/bin/wg-scraper scrape "https://www.wg-gesucht.de/..." 

# Mit Optionen
.env/bin/wg-scraper -v scrape \
  --max-pages 3 \
  --delay 2.0 \
  "https://www.wg-gesucht.de/..."

# Ergebnisse anzeigen
.env/bin/wg-scraper list

# Mit Filter
.env/bin/wg-scraper list --city Berlin --limit 20
```

## 📋 Implementierungs-Aufgaben

Bevor der Scraper produktiv genutzt werden kann, müssen folgende TODOs erledigt werden:

### In `src/wg_scraper/scraper.py`:

1. **`_parse_listing_preview()`**
   - [ ] HTML-Selektoren für Listing-Container identifizieren
   - [ ] Titel-Extraktion implementieren
   - [ ] Preis-Extraktion implementieren
   - [ ] Größen-Extraktion implementieren
   - [ ] Stadt-Extraktion implementieren
   - [ ] Weitere Felder ergänzen

2. **`_get_next_page_url()`**
   - [ ] Pagination-Button identifizieren
   - [ ] Next-URL korrekt extrahieren
   - [ ] End-of-Results erkennen

3. **`_extract_listing_id()`**
   - [ ] URL-Format von wg-gesucht.de analysieren
   - [ ] ID-Extraktion implementieren

4. **`scrape_listing_details()` (Optional)**
   - [ ] Detail-Seite scrapen
   - [ ] Vollständige Beschreibung extrahieren
   - [ ] Bilder extrahieren
   - [ ] Kontakt-Informationen extrahieren

### In `src/wg_scraper/config.py`:

5. **CSS-Selektoren aktualisieren**
   - [ ] Reale Selektoren von wg-gesucht.de eintragen
   - [ ] Im Browser mit DevTools testen

## 🔧 Entwicklungs-Workflow

### 1. Website analysieren
```bash
# Website im Browser öffnen und DevTools nutzen (F12)
# Rechtsklick auf Element → "Untersuchen"
# CSS-Selektoren notieren
```

### 2. Selektoren in config.py eintragen
```python
SELECTORS = {
    "listing_container": "div.actual-class-name",
    # ... weitere Selektoren
}
```

### 3. Scraper implementieren
```bash
# Datei öffnen
code src/wg_scraper/scraper.py

# TODOs suchen und implementieren
```

### 4. Mit einer Seite testen
```bash
# Verbose-Modus für Debug-Output
.env/bin/wg-scraper -vv scrape --max-pages 1 "URL"
```

### 5. Ergebnisse prüfen
```bash
# Datenbank prüfen
.env/bin/wg-scraper list
.env/bin/wg-scraper stats

# Oder direkt in SQLite
sqlite3 wg_data.db "SELECT * FROM listings;"
```

## 🧪 Tests schreiben

```bash
# Test-Datei erstellen
code tests/test_scraper.py

# Tests ausführen
.env/bin/pytest tests/

# Mit Coverage
.env/bin/pytest --cov=wg_scraper tests/
```

## 📚 Weitere Ressourcen

- **Vollständige Dokumentation**: [README_USAGE.md](README_USAGE.md)
- **Beispiel-Code**: [examples.py](examples.py)
- **Konfiguration**: [src/wg_scraper/config.py](src/wg_scraper/config.py)

## ⚖️ Rechtliche Hinweise

- Respektiere robots.txt
- Verwende angemessene Delays (Standard: 1s)
- Nur für private, nicht-kommerzielle Nutzung
- Beachte Nutzungsbedingungen von wg-gesucht.de

## 💡 Tipps

1. **Klein anfangen**: Teste mit `--max-pages 1`
2. **Debug-Modus nutzen**: `-vv` für detaillierte Logs
3. **Browser DevTools**: Unverzichtbar für Selektor-Auswahl
4. **Backup**: Sichere die Datenbank regelmäßig
5. **Rate Limiting**: Erhöhe `--delay` bei Problemen

## 🐛 Fehlersuche

### CLI-Befehl nicht gefunden
```bash
# Virtual Environment aktivieren
source .env/bin/activate

# Oder direkter Pfad
.env/bin/wg-scraper --help
```

### Import-Fehler
```bash
# Neu installieren
.env/bin/pip install -e .
```

### Scraping funktioniert nicht
```bash
# Debug-Modus aktivieren
.env/bin/wg-scraper -vv scrape "URL"

# Logs prüfen und Selektoren anpassen
```

## 📞 Support

Bei Fragen oder Problemen:
- Issue auf GitHub erstellen
- Jonas kontaktieren: jvormstein@outlook.de

---

**Status**: ✅ Grundstruktur fertig | ⏳ Scraping-Implementierung ausstehend

Viel Erfolg! 🎉
