"""
Web-Scraper für wg-gesucht.de.

Dieses Modul enthält die Logik zum Scrapen von WG-Anzeigen.
"""

import logging
import re
import time
from typing import List, Optional, Generator, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from wg_scraper.models import WGListing
from wg_scraper import config

_logger = logging.getLogger(__name__)


class WGScraper:
    """
    Scraper für wg-gesucht.de.
    
    Wichtig: Die Implementierung muss an die tatsächliche Struktur 
    der Website angepasst werden. Dies ist ein Grundgerüst.
    """
    
    BASE_URL = "https://www.wg-gesucht.de"
    
    def __init__(self, delay: float = 1.0):
        """
        Initialisiert den Scraper.
        
        Args:
            delay: Verzögerung zwischen Requests in Sekunden (Standard: 1.0)
        """
        self.delay = delay
        self.session = requests.Session()
        
        # User-Agent setzen, um nicht als Bot erkannt zu werden
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        })
        
        _logger.info(f"Scraper initialisiert mit {delay}s Delay")
    
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Ruft eine Seite ab und parst sie mit BeautifulSoup.
        
        Args:
            url: URL der abzurufenden Seite
            
        Returns:
            BeautifulSoup-Objekt oder None bei Fehler
        """
        try:
            _logger.debug(f"Rufe Seite ab: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Verzögerung einhalten
            time.sleep(self.delay)
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.exceptions.RequestException as e:
            _logger.error(f"Fehler beim Abrufen von {url}: {e}")
            return None
    
    def _extract_listing_id(self, url: str) -> Optional[str]:
        """
        Extrahiert die Listing-ID aus einer URL.
        
        URL-Format: https://www.wg-gesucht.de/wg-zimmer-in-Stadt.123456.html
        
        Args:
            url: URL der Anzeige
            
        Returns:
            Listing-ID oder None
        """
        try:
            # Muster: Stadt.LISTING_ID.html
            match = re.search(r'\.([0-9]+)\.html', url)
            if match:
                return match.group(1)
            
            _logger.warning(f"Konnte ID nicht aus URL extrahieren: {url}")
        except Exception as e:
            _logger.warning(f"Fehler beim ID-Extrahieren von {url}: {e}")
        
        return None
    
    def _parse_number(self, text: Optional[str]) -> Optional[float]:
        """
        Extrahiert eine Zahl aus einem Text.
        
        Args:
            text: Text mit Zahl (z.B. "450 €", "20 m²")
            
        Returns:
            Extrahierte Zahl oder None
        """
        if not text:
            return None
        
        try:
            # Finde erste Zahl im Text (auch mit Dezimalstellen)
            match = re.search(r'([0-9]+[,.]?[0-9]*)', text.replace('.', '').replace(',', '.'))
            if match:
                return float(match.group(1))
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _parse_address(self, address_text: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parst die Adresse im Format: '(Uninteressant) | Stadt/Stadtteil | Straße & Hausnummer'
        
        Args:
            address_text: Adress-String
            
        Returns:
            Tuple (city, district, street)
        """
        if not address_text:
            return None, None, None
        
        try:
            parts = [p.strip() for p in address_text.split('|')]
            
            city = None
            district = None
            street = None
            
            if len(parts) >= 2:
                # Stadt/Stadtteil
                city_parts = parts[1].split('/')
                if len(city_parts) >= 1:
                    city = city_parts[0].strip()
                if len(city_parts) >= 2:
                    district = city_parts[1].strip()
            
            if len(parts) >= 3:
                # Straße
                street = parts[2].strip()
            
            return city, district, street
            
        except Exception as e:
            _logger.warning(f"Fehler beim Parsen der Adresse '{address_text}': {e}")
            return None, None, None
    
    def _parse_neighbors(self, neighbors_title: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
        """
        Parst Mitbewohner-Info im Format: 'Xer WG (Yw,Ym,Yd,Yn)'
        
        Args:
            neighbors_title: Title-Attribut mit Mitbewohner-Info
            
        Returns:
            Tuple (wg_size, flatmate_details)
        """
        if not neighbors_title:
            return None, None
        
        try:
            # Extrahiere WG-Größe (z.B. "3er WG")
            wg_size_match = re.search(r'([0-9]+)er WG', neighbors_title)
            wg_size = int(wg_size_match.group(1)) if wg_size_match else None
            
            # Flatmate-Details (in Klammern)
            flatmates = re.search(r'\(([^)]+)\)', neighbors_title)
            flatmate_details = flatmates.group(1) if flatmates else None
            
            return wg_size, flatmate_details
            
        except Exception as e:
            _logger.warning(f"Fehler beim Parsen der Mitbewohner-Info '{neighbors_title}': {e}")
            return None, None
    
    def _parse_listing_preview(self, element) -> Optional[WGListing]:
        """
        Parst eine Anzeigen-Vorschau aus den Suchergebnissen.
        
        Args:
            element: BeautifulSoup-Element der Anzeigen-Vorschau
            
        Returns:
            WGListing-Objekt oder None bei Fehler
        """
        try:
            selectors = config.SELECTORS
            
            # URL und ID extrahieren
            link_elem = element.select_one(selectors['listing_link'])
            if not link_elem or 'href' not in link_elem.attrs:
                _logger.debug("Kein Link gefunden")
                return None
            
            url = urljoin(self.BASE_URL, link_elem['href'])
            listing_id = self._extract_listing_id(url)
            
            if not listing_id:
                _logger.warning(f"Konnte keine ID für URL {url} extrahieren")
                return None
            
            # Titel extrahieren
            title_elem = element.select_one(selectors['listing_title'])
            title = title_elem.text.strip() if title_elem else "Kein Titel"
            
            # Adresse parsen (Stadt/Stadtteil/Straße)
            address_elem = element.select_one(selectors['listing_address'])
            address_text = address_elem.text.strip() if address_elem else None
            city, district, street = self._parse_address(address_text)
            
            # Größe extrahieren
            size_elem = element.select_one(selectors['listing_size'])
            size = self._parse_number(size_elem.text if size_elem else None)
            
            # Miete extrahieren
            rent_elem = element.select_one(selectors['listing_rent'])
            rent = self._parse_number(rent_elem.text if rent_elem else None)
            
            # Verfügbarkeit
            available_elem = element.select_one(selectors['listing_available'])
            available_from = available_elem.text.strip() if available_elem else None
            
            # Mitbewohner (aus title-Attribut!)
            neighbors_elem = element.select_one(selectors['listing_neighbors'])
            neighbors_title = neighbors_elem.get('title') if neighbors_elem else None
            wg_size, flatmate_details = self._parse_neighbors(neighbors_title)
            
            listing = WGListing(
                listing_id=listing_id,
                url=url,
                title=title,
                city=city,
                district=district,
                size=size,
                rent=rent,
                available_from=available_from,
                flatmates=wg_size,
                flatmate_details=flatmate_details
            )
            
            _logger.debug(f"Listing geparst: {listing}")
            return listing
            
        except Exception as e:
            _logger.error(f"Fehler beim Parsen eines Listings: {e}", exc_info=True)
            return None
    
    def _get_next_page_url(self, current_url: str, current_page: int) -> Optional[str]:
        """
        Erstellt die URL der nächsten Seite.
        
        URL-Format: Stadt.124.0.1.X.html?filter=...
        Nur die Seitenzahl (X) wird erhöht, rest bleibt gleich.
        
        Args:
            current_url: URL der aktuellen Seite
            current_page: Aktuelle Seitenzahl (0-basiert)
            
        Returns:
            URL der nächsten Seite oder None bei Format-Fehler
        """
        try:
            # Finde das Muster: .X.html
            # Beispiel: Stuttgart.124.0.1.0.html?sort_column=3
            match = re.search(r'(.*\.[0-9]+\.[0-9]+\.[0-9]+\.)([0-9]+)(\.html.*)', current_url)
            
            if not match:
                _logger.warning(f"Konnte Seitenzahl-Muster in URL nicht finden: {current_url}")
                return None
            
            # Baue neue URL mit inkrementierter Seitenzahl
            next_page = current_page + 1
            next_url = f"{match.group(1)}{next_page}{match.group(3)}"
            
            _logger.debug(f"Nächste Seite: {next_url}")
            return next_url
            
        except Exception as e:
            _logger.error(f"Fehler beim Erstellen der nächsten Seiten-URL: {e}")
            return None
    
    def scrape_search_results(
        self, 
        start_url: str, 
        max_pages: Optional[int] = None
    ) -> Generator[WGListing, None, None]:
        """
        Scrapt alle Anzeigen aus den Suchergebnissen.
        
        Iteriert durch alle Seiten der Suchergebnisse und gibt
        WGListing-Objekte zurück.
        
        Args:
            start_url: URL der ersten Suchergebnis-Seite
            max_pages: Maximale Anzahl zu scrapender Seiten (None = alle)
            
        Yields:
            WGListing-Objekte
        """
        current_url = start_url
        page_num = 0
        total_listings = 0
        
        _logger.info(f"Starte Scraping von: {start_url}")
        
        while current_url:
            # Prüfe maximale Seitenanzahl
            if max_pages and page_num >= max_pages:
                _logger.info(f"Maximale Seitenanzahl ({max_pages}) erreicht")
                break
            
            _logger.info(f"Scrape Seite {page_num + 1}: {current_url}")
            
            # Seite abrufen
            soup = self._get_page(current_url)
            if not soup:
                _logger.error(f"Konnte Seite {page_num + 1} nicht abrufen")
                break
            
            # Listings auf der Seite finden
            listing_elements = soup.select(config.SELECTORS['listing_container'])
            
            if not listing_elements:
                _logger.warning(f"Keine Listings auf Seite {page_num + 1} gefunden - Ende erreicht?")
                break
            
            _logger.info(f"Gefundene Listings auf Seite {page_num + 1}: {len(listing_elements)}")
            
            # Jedes Listing parsen
            for element in listing_elements:
                listing = self._parse_listing_preview(element)
                if listing:
                    total_listings += 1
                    yield listing
            
            # Zur nächsten Seite
            page_num += 1
            current_url = self._get_next_page_url(current_url, page_num)
        
        _logger.info(
            f"Scraping abgeschlossen: {total_listings} Listings "
            f"von {page_num} Seite(n) gescrapt"
        )
    
    def scrape_listing_details(self, listing: WGListing) -> WGListing:
        """
        Scrapt detaillierte Informationen zu einer Anzeige.
        
        Lädt die Detailseite und extrahiert zusätzliche Beschreibungen.
        
        Args:
            listing: WGListing mit mindestens URL
            
        Returns:
            Aktualisiertes WGListing mit zusätzlichen Details
        """
        _logger.debug(f"Scrape Details für {listing.listing_id}")
        
        soup = self._get_page(listing.url)
        if not soup:
            return listing
        
        try:
            selectors = config.SELECTORS
            descriptions = []
            
            # Verschiedene Beschreibungs-Bereiche sammeln
            for key in ['detail_description', 'detail_desc_location', 
                        'detail_desc_social', 'detail_desc_other']:
                if key in selectors:
                    elems = soup.select(selectors[key])
                    if elems:
                        text = '\n'.join(elem.text.strip() for elem in elems if elem.text.strip())
                        if text:
                            descriptions.append(text)
            
            # Kombinierte Beschreibung
            if descriptions:
                listing.description = '\n\n'.join(descriptions)
                _logger.debug(f"Beschreibung gescrapt: {len(listing.description)} Zeichen")
            
        except Exception as e:
            _logger.warning(f"Fehler beim Scrapen der Details: {e}")
        
        return listing
    
    def close(self):
        """Schließt die Session."""
        self.session.close()
        _logger.debug("Scraper-Session geschlossen")
