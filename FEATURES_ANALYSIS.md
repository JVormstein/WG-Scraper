# WG-Scraper - Neue Features (Analyse & Routing)

## 🆕 Changelog

### Neue Commands

#### 1. Verbesserter `list` Command

**Neue Features:**
- ✅ Flexible Filter mit Operatoren
- ✅ Sortierung nach beliebigen Feldern
- ✅ Verbose-Modi (-v/-vv) für mehr Details
- ✅ Sehr kompakte Default-Ausgabe

**Alte Filter entfernt:** `--city`, `--min-size`, `--max-rent` → Ersetzt durch `--filter`

#### 2. Neuer `route` Command  

Berechnet Distanzen und Routen von WG-Anzeigen zu einem Zielort.

**Features:**
- ✅ Luftlinien-Distanz
- ✅ Fahrstrecke (Auto/Fahrrad/Zu Fuß)
- ✅ Fahrzeit-Schätzung
- ✅ Sortierung nach Entfernung
- ✅ Filter-Unterstützung

---

## 📖 Neue Verwendung

### List Command

#### Basis-Ausgabe
```bash
wg-scraper list --limit 10
```

**Zeigt:** Titel, Stadt, Größe, Miete, Verfügbarkeit, URL

#### Mit Details (-v)
```bash
wg-scraper -v list --limit 5
```

**Zeigt zusätzlich:** WG-Größe, Mitbewohner, Zimmerart, Beschreibung (gekürzt)

#### Mit DB-Metadaten (-vv)
```bash
wg-scraper -vv list --limit 5
```

**Zeigt zusätzlich:** DB-ID, Listing-ID, Scraping-Zeitpunkt, Erstellungs-Zeitpunkt

---

### Filter-System

#### Syntax
```
--filter "feld operator wert"
```

**Operatoren:**
- `=` - Exakt gleich
- `>` - Größer als
- `<` - Kleiner als
- `>=` - Größer oder gleich
- `<=` - Kleiner oder gleich
- `!=` - Nicht gleich

**Mehrere Filter:** Mit Semikolon trennen: `"filter1;filter2;filter3"`

#### Beispiele

```bash
# Miete unter 500€
wg-scraper list --filter "rent<500"

# Größe über 20m²
wg-scraper list --filter "size>20"

# Kombiniert: Größe mindestens 20m², Miete max 600€
wg-scraper list --filter "size>=20;rent<=600"

# Exakte Stadt
wg-scraper list --filter "city=Berlin"

# Mehrere Kriterien
wg-scraper list --filter "city=München;size>25;rent<800"
```

---

### Sortierung

```bash
# Nach Miete aufsteigend
wg-scraper list --sort rent --order asc

# Nach Größe absteigend (größte zuerst)
wg-scraper list --sort size --order desc

# Nach Scraping-Zeit (neueste zuerst) - Standard
wg-scraper list --sort scraped_at --order desc
```

**Sortierbare Felder:**
- `rent` - Miete
- `size` - Größe
- `city` - Stadt (alphabetisch)
- `scraped_at` - Scraping-Zeitpunkt
- `created_at` - DB-Erstellungs-Zeitpunkt
- `available_from` - Verfügbarkeit

---

## 🗺️ Route Command

Berechnet Distanzen und Routen zu einem Ziel.

### Basis-Verwendung

```bash
wg-scraper route "Marienplatz München"
```

**Ausgabe:**
- Luftlinien-Distanz
- Fahrstrecke (Auto, Standard)
- Geschätzte Fahrzeit

### Mit Verkehrsmittel

```bash
# Mit dem Fahrrad
wg-scraper route "Hauptbahnhof Stuttgart" --mode cycling

# Zu Fuß
wg-scraper route "TU Berlin" --mode walking

# Mit dem Auto (Standard)
wg-scraper route "Alexanderplatz" --mode driving
```

**Verfügbare Modi:**
- `driving` / `car` - Auto
- `cycling` / `bike` - Fahrrad
- `walking` / `foot` - Zu Fuß

### Mit Filtern

```bash
# Nur günstige Wohnungen prüfen
wg-scraper route "Hauptbahnhof" --filter "rent<600"

# Nur große Zimmer
wg-scraper route "Uni Campus" --filter "size>25"

# Kombiniert
wg-scraper route "Arbeitsplatz" --filter "rent<700;size>=20"
```

### Sortierung nach Entfernung

```bash
# Sortiere nach Luftlinie (nächste zuerst)
wg-scraper route "Zielort" --sort-by-distance
```

### Limit anpassen

```bash
# Nur 10 Anzeigen prüfen (schneller)
wg-scraper route "Hauptbahnhof" --limit 10

# 50 Anzeigen prüfen
wg-scraper route "Uni" --limit 50
```

---

## 💡 Praktische Beispiele

### Beispiel 1: Günstige WGs nahe der Uni

```bash
# Schritt 1: Filtern und sortieren
wg-scraper list --filter "rent<550;size>=18" --sort rent --order asc --limit 20

# Schritt 2: Route zur Uni berechnen
wg-scraper route "Universität Stuttgart" \
  --filter "rent<550;size>=18" \
  --mode cycling \
  --sort-by-distance
```

### Beispiel 2: Große Zimmer mit kurzer Pendelzeit

```bash
wg-scraper route "Mein Arbeitsplatz, Adresse 123" \
  --filter "size>25" \
  --mode driving \
  --sort-by-distance \
  --limit 15
```

### Beispiel 3: Analyse mit maximalen Details

```bash
wg-scraper -vv list \
  --filter "city=Berlin;rent<=700" \
  --sort size \
  --order desc \
  --limit 5
```

---

## 🔧 Technische Details

### Geocoding & Routing

- **Geocoding:** Nominatim (OpenStreetMap)
- **Routing:** OSRM (Open Source Routing Machine)
- **Beide Services:** Kostenlos, kein API-Key erforderlich

### Filter-Parser

Implementiert in `cli_utils.py`:
```python
from wg_scraper.cli_utils import parse_filters

filters = parse_filters("size>20;rent<500")
# → {'size>': 20, 'rent<': 500}
```

### Routing-Funktion

```python
from wg_scraper.cli_utils import calculate_route

result = calculate_route(
    origin=(48.7758, 9.1829),      # Stuttgart
    destination=(48.7784, 9.1800),  # Hauptbahnhof
    mode='cycling'
)
# → {'straight_line_km': 0.52, 'distance_km': 0.65, 'duration_min': 3.2}
```

---

## 📊 Performance-Tipps

### Route Command

- **Geocoding dauert:** ~1-2 Sekunden pro Adresse
- **Progressbar zeigt:** Fortschritt während Berechnung
- **Limit reduzieren:** Für schnellere Tests `--limit 10`

### Filter

- Filter werden **direkt in SQL** angewendet → sehr schnell
- Auch bei 1000+ Listings keine Performance-Probleme

---

## 🆚 Vorher / Nachher

### Vorher (alte Filter)
```bash
# Limitiert und unflexibel
wg-scraper list --city Berlin --min-size 20 --max-rent 500
```

### Nachher (neue Filter)
```bash
# Flexibel und kombinierbar
wg-scraper list --filter "city=Berlin;size>=20;rent<=500"

# Plus Sortierung
wg-scraper list \
  --filter "city=Berlin;size>=20;rent<=500" \
  --sort rent \
  --order asc
```

---

## 🚀 Nächste Schritte

Mögliche Erweiterungen:

1. **Export-Funktion:**
   ```bash
   wg-scraper list --filter "..." --export csv
   ```

2. **Radius-Filter:**
   ```bash
   wg-scraper list --near "Hauptbahnhof" --radius 5km
   ```

3. **Score-System:**
   ```bash
   wg-scraper score --weights "rent=0.3,distance=0.5,size=0.2"
   ```

4. **Öffentliche Verkehrsmittel** (benötigt API-Key):
   - Google Maps API
   - HERE API
   - Etc.

---

## 📝 Migration von alten Befehlen

### Alte Commands → Neue Commands

| Alt | Neu |
|-----|-----|
| `--city Berlin` | `--filter "city=Berlin"` |
| `--min-size 20` | `--filter "size>=20"` |
| `--max-rent 500` | `--filter "rent<=500"` |
| Kombiniert | `--filter "city=Berlin;size>=20;rent<=500"` |

**Vorteil:** Neue Syntax unterstützt alle Felder und alle Operatoren!

---

## 🐛 Troubleshooting

### "Konnte Adresse nicht finden"
- Adresse zu unspezifisch
- **Lösung:** Stadt hinzufügen: "Hauptbahnhof, Stuttgart"

### Route-Berechnung langsam
- Viele Anzeigen werden geprüft
- **Lösung:** `--limit` reduzieren oder Filter verwenden

### Geocoding-Fehler
- Nominatim überlastet (selten)
- **Lösung:** Kurz warten und erneut versuchen

---

**Status:** ✅ Vollständig implementiert und getestet!

*Erstellt: 13. Februar 2026*
