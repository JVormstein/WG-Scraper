# Geocoding Cache - Dokumentation

## Übersicht

Die `geocode_address()` Funktion nutzt **automatisch einen persistenten Cache**, um:
- API-Anfragen an Nominatim zu reduzieren
- Die Terms of Service (TOS) von Nominatim einzuhalten
- Die Geschwindigkeit bei wiederholten Anfragen zu erhöhen

## Cache-Funktionalität

### Automatisches Caching

Jede Anfrage an `geocode_address()` wird automatisch gecacht:

```python
from wg_scraper.cli_utils import geocode_address

# Erste Anfrage - API-Request mit Rate Limiting (>1 Sekunde)
coords = geocode_address("Berlin, Deutschland")
# Ergebnis: (52.5200, 13.4050)

# Zweite Anfrage - SOFORT aus Cache (<0.01 Sekunden)
coords = geocode_address("Berlin, Deutschland")
# Ergebnis: (52.5200, 13.4050) [aus Cache]
```

### Cache-Eigenschaften

- **Speicherort**: `~/.wg_scraper_geocoding_cache/`
- **TTL (Time-to-Live)**: 7 Tage
- **Format**: JSON-Dateien mit MD5-Hash als Dateiname
- **Cacht auch**: Negative Resultate (nicht gefundene Adressen)

### Cache-Statistiken anzeigen

```python
from wg_scraper.cli_utils import get_geocoding_cache_stats

stats = get_geocoding_cache_stats()
print(stats)
# {
#   'cache_dir': '/home/user/.wg_scraper_geocoding_cache',
#   'cached_entries': 28,
#   'cache_size_mb': 0.01
# }
```

### Cache leeren

```python
from wg_scraper.cli_utils import clear_geocoding_cache

# Löscht alle gecachten Einträge
clear_geocoding_cache()
```

## Nominatim TOS Konformität

Die Implementierung erfüllt die [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/):

1. ✅ **Rate Limiting**: Mindestens 1 Sekunde zwischen API-Anfragen
2. ✅ **User-Agent**: Aussagekräftig mit Kontaktinformation
3. ✅ **Caching**: Reduziert redundante Anfragen
4. ✅ **Keine Massenlast**: Durch Rate Limiting und Caching

## Verwendung im CLI

Der Cache wird transparent in allen CLI-Befehlen genutzt:

```bash
# Analyse mit Routing - nutzt automatisch den Cache
wg-scraper analyse --route --addr "Universität Stuttgart" --mode transit

# Beim ersten Durchlauf: Langsamer (API-Requests mit Rate Limiting)
# Bei wiederholtem Durchlauf: Schnell (alle Adressen aus Cache)
```

## Performance-Vergleich

| Anfrage | Ohne Cache | Mit Cache |
|---------|-----------|-----------|
| 1. Request | ~1.2s | ~1.2s |
| 2. Request (gleiche Adresse) | ~1.2s | <0.01s |
| 100 Requests (gleiche Adressen) | ~120s | ~1.2s |

## Cache-Struktur

Jeder Cache-Eintrag ist eine JSON-Datei:

```json
{
  "cached_at": "2026-02-15T15:30:45.123456",
  "address": "Berlin, Deutschland",
  "coordinates": [52.52, 13.405]
}
```

Für nicht gefundene Adressen:

```json
{
  "cached_at": "2026-02-15T15:30:45.123456",
  "address": "Nonexistent Street, Nowhere",
  "coordinates": null
}
```

## Häufige Fragen

### Wann wird der Cache automatisch geleert?

Der Cache wird **nicht** automatisch geleert. Einträge bleiben bis:
- TTL abgelaufen ist (7 Tage)
- Manuell mit `clear_geocoding_cache()` gelöscht

### Kann ich den Cache-TTL ändern?

Ja, durch Modifikation des `GeocoderRateLimiter`:

```python
from wg_scraper.cli_utils import GeocoderRateLimiter

# Neuer Geocoder mit 24 Stunden TTL
custom_geocoder = GeocoderRateLimiter(
    min_delay_seconds=1.0,
    cache_ttl_hours=24
)
```

### Was passiert bei Netzwerkfehlern?

Bei Netzwerkfehlern:
1. Fehler wird geloggt
2. `None` wird zurückgegeben
3. **Kein** Cache-Eintrag wird erstellt (für Retry bei nächster Anfrage)

### Wie viel Speicherplatz braucht der Cache?

- Pro Adresse: ~200-500 Bytes
- 1000 Adressen: ~0.5 MB
- Cache ist sehr speichereffizient
