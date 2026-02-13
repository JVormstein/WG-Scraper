"""
Datenbank-Modul für die Speicherung von WG-Anzeigen.

Verwendet SQLite für die lokale Datenspeicherung.
"""

import logging
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any

from wg_scraper.models import WGListing

_logger = logging.getLogger(__name__)


class Database:
    """
    Datenbank-Manager für WG-Anzeigen.
    
    Verwaltet die SQLite-Datenbank mit allen gescrapten Anzeigen.
    """
    
    def __init__(self, db_path: str = "wg_data.db"):
        """
        Initialisiert die Datenbankverbindung.
        
        Args:
            db_path: Pfad zur SQLite-Datenbankdatei
        """
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        _logger.info(f"Datenbank-Manager initialisiert: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Gibt eine Datenbankverbindung zurück.
        
        Returns:
            SQLite-Connection
        """
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Ermöglicht dict-ähnlichen Zugriff
        return self.conn
    
    def init_db(self):
        """
        Initialisiert die Datenbank mit den erforderlichen Tabellen.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Haupttabelle für WG-Anzeigen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                city TEXT,
                district TEXT,
                size REAL,
                rent REAL,
                available_from TEXT,
                available_until TEXT,
                room_type TEXT,
                online_since TEXT,
                description TEXT,
                flatmates INTEGER,
                flatmate_details TEXT,
                features TEXT,
                images TEXT,
                contact_name TEXT,
                scraped_at TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index für schnellere Suchen
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_city ON listings(city)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rent ON listings(rent)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scraped_at ON listings(scraped_at)
        """)
        
        conn.commit()
        _logger.info("Datenbank initialisiert")
    
    def save_listing(self, listing: WGListing) -> bool:
        """
        Speichert eine WG-Anzeige in der Datenbank.
        
        Wenn eine Anzeige mit der gleichen listing_id bereits existiert,
        wird sie nicht erneut gespeichert.
        
        Args:
            listing: WGListing-Objekt
            
        Returns:
            True wenn gespeichert, False wenn bereits vorhanden
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            data = listing.to_dict()
            
            cursor.execute("""
                INSERT INTO listings (
                    listing_id, url, title, city, district, size, rent,
                    available_from, available_until, room_type, online_since,
                    description, flatmates, flatmate_details, features,
                    images, contact_name, scraped_at
                ) VALUES (
                    :listing_id, :url, :title, :city, :district, :size, :rent,
                    :available_from, :available_until, :room_type, :online_since,
                    :description, :flatmates, :flatmate_details, :features,
                    :images, :contact_name, :scraped_at
                )
            """, data)
            
            conn.commit()
            _logger.debug(f"Listing {listing.listing_id} gespeichert")
            return True
            
        except sqlite3.IntegrityError:
            _logger.debug(f"Listing {listing.listing_id} bereits vorhanden")
            return False
        except Exception as e:
            _logger.error(f"Fehler beim Speichern von Listing {listing.listing_id}: {e}")
            conn.rollback()
            return False
    
    def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Ruft eine einzelne Anzeige anhand der listing_id ab.
        
        Args:
            listing_id: ID der Anzeige
            
        Returns:
            Dictionary mit Anzeigendaten oder None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM listings WHERE listing_id = ?",
            (listing_id,)
        )
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_listings(
        self,
        limit: int = 100,
        offset: int = 0,
        city: Optional[str] = None,
        min_size: Optional[float] = None,
        max_rent: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Ruft mehrere Anzeigen mit optionalen Filtern ab.
        
        Args:
            limit: Maximale Anzahl der Ergebnisse
            offset: Offset für Pagination
            city: Filter nach Stadt
            min_size: Minimale Größe in m²
            max_rent: Maximale Miete in Euro
            
        Returns:
            Liste von Dictionaries mit Anzeigendaten
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM listings WHERE 1=1"
        params = []
        
        if city:
            query += " AND city = ?"
            params.append(city)
        
        if min_size:
            query += " AND size >= ?"
            params.append(min_size)
        
        if max_rent:
            query += " AND rent <= ?"
            params.append(max_rent)
        
        query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Berechnet Statistiken über die gespeicherten Anzeigen.
        
        Returns:
            Dictionary mit Statistiken
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Gesamtzahl
        cursor.execute("SELECT COUNT(*) as total FROM listings")
        total = cursor.fetchone()['total']
        
        # Anzahl verschiedener Städte
        cursor.execute("SELECT COUNT(DISTINCT city) as cities FROM listings WHERE city IS NOT NULL")
        cities = cursor.fetchone()['cities']
        
        # Durchschnittliche Miete
        cursor.execute("SELECT AVG(rent) as avg_rent FROM listings WHERE rent IS NOT NULL")
        avg_rent = cursor.fetchone()['avg_rent'] or 0
        
        # Durchschnittliche Größe
        cursor.execute("SELECT AVG(size) as avg_size FROM listings WHERE size IS NOT NULL")
        avg_size = cursor.fetchone()['avg_size'] or 0
        
        # Top 5 Städte
        cursor.execute("""
            SELECT city, COUNT(*) as count 
            FROM listings 
            WHERE city IS NOT NULL 
            GROUP BY city 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_cities = [(row['city'], row['count']) for row in cursor.fetchall()]
        
        return {
            'total': total,
            'cities': cities,
            'avg_rent': avg_rent,
            'avg_size': avg_size,
            'top_cities': top_cities
        }
    
    def delete_listing(self, listing_id: str) -> bool:
        """
        Löscht eine Anzeige aus der Datenbank.
        
        Args:
            listing_id: ID der zu löschenden Anzeige
            
        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM listings WHERE listing_id = ?", (listing_id,))
        conn.commit()
        
        deleted = cursor.rowcount > 0
        if deleted:
            _logger.info(f"Listing {listing_id} gelöscht")
        else:
            _logger.warning(f"Listing {listing_id} nicht gefunden")
        
        return deleted
    
    def clear_all(self):
        """
        Löscht alle Anzeigen aus der Datenbank.
        
        ACHTUNG: Diese Aktion kann nicht rückgängig gemacht werden!
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM listings")
        conn.commit()
        
        _logger.warning("Alle Listings aus der Datenbank gelöscht")
    
    def close(self):
        """Schließt die Datenbankverbindung."""
        if self.conn:
            self.conn.close()
            self.conn = None
            _logger.debug("Datenbankverbindung geschlossen")
    
    def __enter__(self):
        """Context-Manager-Unterstützung."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context-Manager-Unterstützung."""
        self.close()
