"""Pydantic models for Thai ID Card data."""

from datetime import date, datetime
from pathlib import Path
from typing import Optional

from dateutil.parser import parse as parse_date
from pydantic import BaseModel, Field, field_validator, computed_field


class ThaiIDCard(BaseModel):
    """Model representing data from a Thai National ID Card."""

    cid: str = Field(
        ..., 
        description="13-digit citizen identification number",
        min_length=13,
        max_length=13,
        pattern=r"^\d{13}$"
    )
    thai_fullname: str = Field(
        ..., 
        description="Full name in Thai language"
    )
    english_fullname: str = Field(
        ..., 
        description="Full name in English"
    )
    date_of_birth: date = Field(
        ..., 
        description="Date of birth"
    )
    gender: str = Field(
        ..., 
        description="Gender (1=Male, 2=Female)",
        pattern=r"^[12]$"
    )
    card_issuer: str = Field(
        ..., 
        description="Card issuing organization"
    )
    issue_date: date = Field(
        ..., 
        description="Date when the card was issued"
    )
    expire_date: date = Field(
        ..., 
        description="Date when the card expires"
    )
    address: str = Field(
        ..., 
        description="Registered address"
    )
    photo: Optional[bytes] = Field(
        None, 
        description="JPEG photo data"
    )

    @field_validator("cid")
    @classmethod
    def validate_cid(cls, v: str) -> str:
        """Validate Thai citizen ID with checksum."""
        if not v.isdigit() or len(v) != 13:
            raise ValueError("CID must be exactly 13 digits")
        
        # Calculate checksum (Thai ID card algorithm)
        checksum = 0
        for i in range(12):
            checksum += int(v[i]) * (13 - i)
        checksum = (11 - (checksum % 11)) % 10
        
        if checksum != int(v[12]):
            raise ValueError(f"Invalid CID checksum: expected {checksum}, got {v[12]}")
        
        return v

    @field_validator("date_of_birth", "issue_date", "expire_date", mode="before")
    @classmethod
    def parse_date_field(cls, v: str | date) -> date:
        """Parse date from Thai Buddhist calendar string (YYYYMMDD)."""
        if isinstance(v, date):
            return v
        
        if not v or len(v) != 8:
            raise ValueError(f"Invalid date format: {v}")
        
        # Parse as YYYYMMDD in Buddhist Era
        year = int(v[:4]) - 543  # Convert from Buddhist Era to Gregorian
        month = int(v[4:6])
        day = int(v[6:8])
        
        try:
            return date(year, month, day)
        except ValueError as e:
            raise ValueError(f"Invalid date: {v} - {e}")

    @computed_field
    @property
    def age(self) -> int:
        """Calculate current age from date of birth."""
        today = date.today()
        age = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age

    @computed_field
    @property
    def gender_text(self) -> str:
        """Get gender as text."""
        return "Male" if self.gender == "1" else "Female"

    @computed_field
    @property
    def is_expired(self) -> bool:
        """Check if the card has expired."""
        return date.today() > self.expire_date

    @computed_field
    @property
    def days_until_expiry(self) -> int:
        """Calculate days until card expiry."""
        return (self.expire_date - date.today()).days

    def save_photo(self, path: Optional[Path] = None) -> Optional[Path]:
        """Save photo to file.
        
        Args:
            path: Path to save the photo. If None, saves as {cid}.jpg
            
        Returns:
            Path where photo was saved, or None if no photo data
        """
        if not self.photo:
            return None
        
        if path is None:
            path = Path(f"{self.cid}.jpg")
        
        path.write_bytes(self.photo)
        return path

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            date: lambda v: v.isoformat(),
            bytes: lambda v: None  # Don't include photo in JSON
        }


class CardReaderInfo(BaseModel):
    """Information about a smart card reader."""
    
    index: int = Field(..., description="Reader index in the system")
    name: str = Field(..., description="Reader name/model")
    atr: Optional[str] = Field(None, description="Answer to Reset (ATR) hex string")
    connected: bool = Field(False, description="Whether a card is connected")