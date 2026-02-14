"""
Datenmodelle für WG-Anzeigen.

Definiert die Struktur der gescrapten Daten.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class WGListing:
    """
    Repräsentiert eine WG-Anzeige von wg-gesucht.de.
    
    Attributes:
        listing_id: Eindeutige ID der Anzeige auf wg-gesucht.de
        url: URL zur Anzeigendetails
        title: Titel der Anzeige
        city: Stadt
        district: Stadtteil/Bezirk
        size: Größe des Zimmers in m²
        rent: Miete (warm) in Euro
        available_from: Verfügbar ab (Datum)
        available_until: Verfügbar bis (Datum), optional
        room_type: Art des Zimmers (z.B. "WG-Zimmer", "1-Zimmer-Wohnung")
        online_since: Datum, seit wann die Anzeige online ist
        description: Beschreibungstext der Anzeige
        flatmates: Anzahl der Mitbewohner
        flatmate_details: Details zu Mitbewohnern (Alter, Geschlecht, etc.)
        flatmates_female: Anzahl weiblicher Mitbewohner
        flatmates_male: Anzahl maennlicher Mitbewohner
        flatmates_diverse: Anzahl diverser Mitbewohner
        rooms_free: Anzahl freier Zimmer
        features: Liste von Ausstattungsmerkmalen
        images: Liste von Bild-URLs
        contact_name: Name des Ansprechpartners
        scraped_at: Zeitpunkt des Scrapings
    """
    
    # Pflichtfelder
    listing_id: str
    url: str
    title: str
    
    # Optionale Felder
    city: Optional[str] = None
    district: Optional[str] = None
    size: Optional[float] = None
    rent: Optional[float] = None
    available_from: Optional[str] = None
    available_until: Optional[str] = None
    room_type: Optional[str] = None
    online_since: Optional[str] = None
    description: Optional[str] = None
    flatmates: Optional[int] = None
    flatmate_details: Optional[str] = None
    flatmates_female: Optional[int] = None
    flatmates_male: Optional[int] = None
    flatmates_diverse: Optional[int] = None
    rooms_free: Optional[int] = None
    features: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    contact_name: Optional[str] = None
    scraped_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """
        Konvertiert das Listing in ein Dictionary.
        
        Returns:
            Dictionary mit allen Feldern
        """
        return {
            'listing_id': self.listing_id,
            'url': self.url,
            'title': self.title,
            'city': self.city,
            'district': self.district,
            'size': self.size,
            'rent': self.rent,
            'available_from': self.available_from,
            'available_until': self.available_until,
            'room_type': self.room_type,
            'online_since': self.online_since,
            'description': self.description,
            'flatmates': self.flatmates,
            'flatmate_details': self.flatmate_details,
            'flatmates_female': self.flatmates_female,
            'flatmates_male': self.flatmates_male,
            'flatmates_diverse': self.flatmates_diverse,
            'rooms_free': self.rooms_free,
            'features': ','.join(self.features) if self.features else None,
            'images': ','.join(self.images) if self.images else None,
            'contact_name': self.contact_name,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WGListing':
        """
        Erstellt ein WGListing aus einem Dictionary.
        
        Args:
            data: Dictionary mit Listing-Daten
            
        Returns:
            WGListing-Instanz
        """
        # Konvertiere komma-separierte Strings zurück in Listen
        if 'features' in data and isinstance(data['features'], str):
            data['features'] = data['features'].split(',') if data['features'] else []
        if 'images' in data and isinstance(data['images'], str):
            data['images'] = data['images'].split(',') if data['images'] else []
        
        # Konvertiere scraped_at String zurück zu datetime
        if 'scraped_at' in data and isinstance(data['scraped_at'], str):
            data['scraped_at'] = datetime.fromisoformat(data['scraped_at'])
        
        return cls(**data)
    
    def __str__(self) -> str:
        """String-Repräsentation des Listings."""
        return (
            f"WGListing(id={self.listing_id}, "
            f"title='{self.title}', "
            f"city='{self.city}', "
            f"rent={self.rent}€, "
            f"size={self.size}m²)"
        )
    
    def __repr__(self) -> str:
        """Detaillierte Repräsentation."""
        return self.__str__()
