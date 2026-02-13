# CSS-Selektoren Guide für WG-Scraper

## 📖 Grundlagen

CSS-Selektoren werden verwendet, um HTML-Elemente auf einer Webseite zu finden.

### Wichtigste Syntax-Regeln

| Syntax | Bedeutung | Beispiel | Findet |
|--------|-----------|----------|--------|
| `tag` | HTML-Tag | `div`, `a`, `span` | Alle `<div>`, `<a>`, `<span>` |
| `.class` | CSS-Klasse | `.headline`, `.btn` | Elemente mit `class="headline"` |
| `#id` | ID | `#main`, `#header` | Element mit `id="main"` |
| `tag.class` | Tag mit Klasse | `div.container`, `a.link` | `<div class="container">` |
| `parent child` | Nachfahre | `div a` | `<a>` irgendwo in `<div>` |
| `parent > child` | Direktes Kind | `div > a` | `<a>` direkt unter `<div>` |
| `[attr]` | Attribut | `a[href]`, `img[src]` | Links mit href, Bilder mit src |
| `[attr="val"]` | Attribut-Wert | `a[href="/home"]` | Links zu "/home" |
| `:nth-of-type(n)` | n-tes Element | `div:nth-of-type(2)` | 2. `<div>` |

## ❌ Häufige Fehler

### Fehler 1: Punkt vor HTML-Tag
```python
# ❌ FALSCH
"div.a"  # Sucht nach <div class="a">, nicht nach <a>!
"h2.truncate_title.a"  # Sucht nach <h2 class="truncate_title a">

# ✅ RICHTIG
"div a"  # Sucht nach <a> in <div>
"h2.truncate_title a"  # Sucht nach <a> in <h2 class="truncate_title">
```

### Fehler 2: Attribute als Klassen
```python
# ❌ FALSCH
"a.href"  # Sucht nach <a class="href">
"img.src"  # Sucht nach <img class="src">

# ✅ RICHTIG
"a[href]"  # Sucht nach <a href="...">
"img[src]"  # Sucht nach <img src="...">
```

### Fehler 3: Mehrere Klassen falsch trennen
```python
# HTML: <div class="card listing active">

# ❌ FALSCH
"div.card.listing active"  # Falsche Mischung

# ✅ RICHTIG
"div.card.listing.active"  # Alle Klassen zusammen
"div.card.listing"  # Nur erste zwei Klassen
```

## 🎯 Praktische Beispiele

### Beispiel 1: Einfacher Container
```html
<div class="offer_list_item">
    <h3 class="headline">Schönes WG-Zimmer</h3>
    <span class="price">450 €</span>
</div>
```

```python
SELECTORS = {
    "listing_container": "div.offer_list_item",
    "listing_title": "h3.headline",  # Relativ zum Container!
    "listing_price": "span.price",
}
```

### Beispiel 2: Verschachtelte Struktur
```html
<div class="listing">
    <div class="header">
        <h2 class="title">
            <a href="/wg/123">WG-Zimmer in Berlin</a>
        </h2>
    </div>
</div>
```

```python
SELECTORS = {
    "listing_container": "div.listing",
    "listing_link": "a[href]",  # Findet <a> irgendwo im Container
    "listing_title_alt": "h2.title a",  # Spezifischer: a in h2
    "listing_title_direct": "h2.title > a",  # Noch spezifischer: direktes Kind
}
```

### Beispiel 3: nth-of-type für gleiche Elemente
```html
<div class="details">
    <div class="col">20 m²</div>
    <div class="col">450 €</div>
    <div class="col">Berlin</div>
</div>
```

```python
SELECTORS = {
    "listing_size": "div.col:nth-of-type(1)",  # Erstes div.col
    "listing_rent": "div.col:nth-of-type(2)",  # Zweites div.col
    "listing_city": "div.col:nth-of-type(3)",  # Drittes div.col
}
```

### Beispiel 4: Attribute mit Bedingungen
```html
<a href="/wg-zimmer">WG-Zimmer</a>
<a href="/1-zimmer-wohnung">Wohnung</a>
```

```python
SELECTORS = {
    "all_links": "a[href]",  # Alle Links mit href
    "wg_links": "a[href*='wg-zimmer']",  # Nur Links mit "wg-zimmer" im href
    "external": "a[href^='https://']",  # Links die mit https:// beginnen
}
```

## 🔍 Hierarchie in WG-Scraper

### Wie Selektoren im Scraper verwendet werden

```python
# 1. Finde alle Container
containers = soup.select(SELECTORS["listing_container"])

# 2. In jedem Container suche Details (RELATIV zum Container!)
for container in containers:
    # Diese Suche findet nur Elemente IN diesem Container
    title = container.select_one(SELECTORS["listing_title"])
    rent = container.select_one(SELECTORS["listing_rent"])
    link = container.select_one(SELECTORS["listing_link"])
```

**Wichtig:** Alle `listing_*` Selektoren (außer `listing_container`) sollten:
- **Relativ** zum Container sein
- **Nicht** den Container selbst enthalten
- **Nur das spezifische Element** beschreiben

### ✅ Gutes Beispiel (relativ)

```python
SELECTORS = {
    "listing_container": "div.offer",
    "listing_title": "h3 a",  # ✅ Findet <a> in <h3> innerhalb des Containers
    "listing_price": "span.price",  # ✅ Findet <span class="price"> im Container
}
```

### ❌ Schlechtes Beispiel (absolut)

```python
SELECTORS = {
    "listing_container": "div.offer",
    "listing_title": "div.offer h3 a",  # ❌ Enthält Container, findet alle auf der Seite!
}
```

## 🛠️ Tipps zum Finden von Selektoren

### 1. Browser DevTools (F12)
1. Webseite öffnen
2. F12 drücken → DevTools
3. Rechtsklick auf Element → "Untersuchen"
4. Element ist im HTML-Code markiert

### 2. Selektoren testen in Browser-Konsole
```javascript
// In der Browser-Konsole (F12 → Console):
document.querySelector("h2.truncate_title a")  // Findet erstes Element
document.querySelectorAll("div.offer_list_item")  // Findet alle Elemente
```

### 3. Copy Selector
1. Element in DevTools auswählen
2. Rechtsklick auf HTML-Code
3. "Copy" → "Copy selector"
4. ⚠️ **Achtung:** Oft zu spezifisch! Vereinfachen!

**Beispiel:**
```
# Browser gibt:
body > div#content > div.main > div.listings > div:nth-child(3) > h2.title > a

# Besser vereinfachen zu:
div.listings h2.title a
# oder noch kürzer:
h2.title a
```

## 📦 Mehrere Klassen kombinieren

```html
<div class="offer listing premium featured">
```

```python
# Alle 4 Klassen müssen vorhanden sein
"div.offer.listing.premium.featured"

# Nur offer und listing (premium/featured egal)
"div.offer.listing"

# Nur eine Klasse (andere egal)
"div.offer"
```

## 🔗 Weitere Ressourcen

- [CSS Selectors Cheat Sheet](https://www.w3schools.com/cssref/css_selectors.asp)
- [BeautifulSoup Dokumentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- Try selectors: [CSS Selector Tester](https://www.w3schools.com/cssref/trysel.php)

## 💡 Für WG-Gesucht.de

Wenn du die Selektoren für wg-gesucht.de anpassen möchtest:

1. **Öffne eine Suchergebnis-Seite** im Browser
2. **F12** → DevTools
3. **Rechtsklick** auf eine Anzeige → "Untersuchen"
4. **Identifiziere** die Container-Struktur
5. **Notiere** die Klassen/IDs
6. **Teste** in der Konsole:
   ```javascript
   document.querySelectorAll("div.dein-container-selektor")
   ```
7. **Trage ein** in [config.py](../src/wg_scraper/config.py)
8. **Teste** mit CLI:
   ```bash
   .env/bin/wg-scraper -vv scrape --max-pages 1 "URL"
   ```

Viel Erfolg! 🎉
