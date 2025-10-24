"""Pydantic models for Thai ID Card data."""

from datetime import date
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator, computed_field


class Name(BaseModel):
    """Model representing a Thai name (or English transliteration)."""

    prefix: str = Field(..., description="Name prefix (e.g., นาย, Mr., Mrs.)")
    first_name: str = Field(..., description="First name")
    middle_name: str = Field(default="", description="Middle name (may be empty)")
    last_name: str = Field(..., description="Last name")

    @computed_field
    @property
    def full_name(self) -> str:
        """Get the full name."""
        if self.middle_name:
            return f"{self.prefix}{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.prefix}{self.first_name} {self.last_name}"

    @classmethod
    def from_raw(cls, raw: str) -> "Name":
        """Parse name from raw card data format (prefix#firstname#middlename#lastname).

        Args:
            raw: Raw name string from card with # delimiters

        Returns:
            Name instance
        """
        parts = raw.split("#")
        if len(parts) < 4:
            # Pad with empty strings if not enough parts
            parts.extend([""] * (4 - len(parts)))

        return cls(
            prefix=parts[0].strip(),
            first_name=parts[1].strip(),
            middle_name=parts[2].strip(),
            last_name=parts[3].strip(),
        )


class Address(BaseModel):
    """Model representing a Thai address."""

    house_no: str = Field(..., description="House number (บ้านเลขที่)")
    moo: str = Field(default="", description="Village/Moo number (หมู่ที่)")
    soi: str = Field(default="", description="Soi/Lane (ซอย)")
    street: str = Field(default="", description="Street/Road (ถนน)")
    subdistrict: str = Field(..., description="Subdistrict/Tambon (ตำบล/แขวง)")
    district: str = Field(..., description="District/Amphoe (อำเภอ/เขต)")
    province: str = Field(..., description="Province (จังหวัด)")

    @computed_field
    @property
    def address(self) -> str:
        """Get the full address string."""
        parts = []

        if self.house_no:
            parts.append(self.house_no)
        if self.moo:
            parts.append(
                f"หมู่ที่{self.moo}"
                if self.moo and not self.moo.startswith("หมู่")
                else self.moo
            )
        if self.soi:
            parts.append(
                f"ซอย{self.soi}"
                if self.soi and not self.soi.startswith("ซอย")
                else self.soi
            )
        if self.street:
            parts.append(self.street)
        if self.subdistrict:
            # Handle both ตำบล (rural) and แขวง (Bangkok) prefixes
            if not (
                self.subdistrict.startswith("ตำบล")
                or self.subdistrict.startswith("แขวง")
            ):
                parts.append(f"ตำบล{self.subdistrict}")
            else:
                parts.append(self.subdistrict)
        if self.district:
            # Handle both อำเภอ (rural) and เขต (Bangkok) prefixes
            if not (
                self.district.startswith("อำเภอ") or self.district.startswith("เขต")
            ):
                parts.append(f"อำเภอ{self.district}")
            else:
                parts.append(self.district)
        if self.province:
            parts.append(
                f"จังหวัด{self.province}"
                if not self.province.startswith("จังหวัด")
                else self.province
            )

        return " ".join(parts)

    @classmethod
    def from_raw(cls, raw: str) -> "Address":
        """Parse address from raw card data format.

        The format is: house_no#moo/soi#street_parts...#subdistrict#district#province
        Each part is delimited by #.

        Args:
            raw: Raw address string from card with # delimiters

        Returns:
            Address instance
        """
        parts = raw.split("#")

        # Fallback for non-# delimited addresses
        if len(parts) < 4:
            # Try to extract basic address components from the raw string
            # If the address doesn't use # delimiters, store it as-is
            # Look for common Thai address keywords
            raw_clean = raw.strip()

            # Try to find province (จังหวัด)
            province = ""
            if "จังหวัด" in raw_clean:
                # Extract province from the string
                province_idx = raw_clean.rfind("จังหวัด")
                province = raw_clean[province_idx:].replace("จังหวัด", "").strip()
                # Get everything before province
                raw_clean = raw_clean[:province_idx].strip()

            # Try to find district (อำเภอ or เขต)
            district = ""
            if "อำเภอ" in raw_clean:
                district_idx = raw_clean.rfind("อำเภอ")
                district = (
                    raw_clean[district_idx:].replace("อำเภอ", "").strip().split()[0]
                    if raw_clean[district_idx:].replace("อำเภอ", "").strip()
                    else ""
                )
                raw_clean = raw_clean[:district_idx].strip()
            elif "เขต" in raw_clean:
                district_idx = raw_clean.rfind("เขต")
                district = (
                    raw_clean[district_idx:].replace("เขต", "").strip().split()[0]
                    if raw_clean[district_idx:].replace("เขต", "").strip()
                    else ""
                )
                raw_clean = raw_clean[:district_idx].strip()

            # Try to find subdistrict (ตำบล or แขวง)
            subdistrict = ""
            if "ตำบล" in raw_clean:
                subdistrict_idx = raw_clean.rfind("ตำบล")
                subdistrict = (
                    raw_clean[subdistrict_idx:].replace("ตำบล", "").strip().split()[0]
                    if raw_clean[subdistrict_idx:].replace("ตำบล", "").strip()
                    else ""
                )
                raw_clean = raw_clean[:subdistrict_idx].strip()
            elif "แขวง" in raw_clean:
                subdistrict_idx = raw_clean.rfind("แขวง")
                subdistrict = (
                    raw_clean[subdistrict_idx:].replace("แขวง", "").strip().split()[0]
                    if raw_clean[subdistrict_idx:].replace("แขวง", "").strip()
                    else ""
                )
                raw_clean = raw_clean[:subdistrict_idx].strip()

            # What's left is likely house number, moo, soi, street
            # Just use the remaining as house_no
            house_no = raw_clean if raw_clean else raw.strip()

            # Ensure we have at least minimal required fields
            if not subdistrict:
                subdistrict = "ไม่ระบุ"
            if not district:
                district = "ไม่ระบุ"
            if not province:
                province = "ไม่ระบุ"

            return cls(
                house_no=house_no,
                moo="",
                soi="",
                street="",
                subdistrict=subdistrict,
                district=district,
                province=province,
            )

        house_no = parts[0].strip()
        moo = ""
        soi = ""

        # Parse second part - could be Moo or Soi
        if len(parts) > 1 and parts[1]:
            second_part = parts[1].strip()
            if second_part.startswith("หมู่ที่"):
                moo = second_part.replace("หมู่ที่", "").strip()
            elif second_part.startswith("ซอย"):
                soi = second_part.replace("ซอย", "").strip()
            else:
                # If no prefix, check if it looks like a number (Moo) or name (Soi)
                if second_part.isdigit():
                    moo = second_part
                else:
                    soi = second_part

        # Street is everything between the second part and the last 3 parts
        street_parts = []
        for i in range(2, len(parts) - 3):
            if parts[i].strip():
                street_parts.append(parts[i].strip())
        street = " ".join(street_parts)

        # Last 3 parts are subdistrict, district, province
        subdistrict = parts[-3].strip()
        district = parts[-2].strip()
        province = parts[-1].strip()

        # Remove Thai prefixes for cleaner storage
        if subdistrict.startswith("ตำบล"):
            subdistrict = subdistrict.replace("ตำบล", "").strip()
        elif subdistrict.startswith("แขวง"):
            subdistrict = subdistrict.replace("แขวง", "").strip()

        if district.startswith("อำเภอ"):
            district = district.replace("อำเภอ", "").strip()
        elif district.startswith("เขต"):
            district = district.replace("เขต", "").strip()

        if province.startswith("จังหวัด"):
            province = province.replace("จังหวัด", "").strip()

        return cls(
            house_no=house_no,
            moo=moo,
            soi=soi,
            street=street,
            subdistrict=subdistrict,
            district=district,
            province=province,
        )


class ThaiIDCard(BaseModel):
    """Model representing data from a Thai National ID Card."""

    cid: str = Field(
        ...,
        description="13-digit citizen identification number",
        min_length=13,
        max_length=13,
        pattern=r"^\d{13}$",
    )
    thai_name: Name = Field(..., description="Name in Thai language")
    english_name: Name = Field(..., description="Name in English")
    date_of_birth: date = Field(..., description="Date of birth")
    gender: str = Field(..., description="Gender (1=Male, 2=Female)", pattern=r"^[12]$")
    card_issuer: str = Field(..., description="Card issuing organization")
    issue_date: date = Field(..., description="Date when the card was issued")
    expire_date: date = Field(..., description="Date when the card expires")
    address_info: Address = Field(..., description="Registered address information")
    photo: Optional[bytes] = Field(None, description="JPEG photo data")

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

    @field_validator("thai_name", "english_name", mode="before")
    @classmethod
    def parse_name_field(cls, v: str | Name) -> Name:
        """Parse name from raw string or pass through Name object."""
        if isinstance(v, Name):
            return v
        if isinstance(v, str):
            return Name.from_raw(v)
        raise ValueError(f"Invalid name type: {type(v)}")

    @field_validator("address_info", mode="before")
    @classmethod
    def parse_address_field(cls, v: str | Address) -> Address:
        """Parse address from raw string or pass through Address object."""
        if isinstance(v, Address):
            return v
        if isinstance(v, str):
            return Address.from_raw(v)
        raise ValueError(f"Invalid address type: {type(v)}")

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
    def thai_fullname(self) -> str:
        """Get Thai full name as string (backward compatibility)."""
        return self.thai_name.full_name

    @computed_field
    @property
    def english_fullname(self) -> str:
        """Get English full name as string (backward compatibility)."""
        return self.english_name.full_name

    @computed_field
    @property
    def address(self) -> str:
        """Get full address as string (backward compatibility)."""
        return self.address_info.address

    @computed_field
    @property
    def age(self) -> int:
        """Calculate current age from date of birth."""
        today = date.today()
        age = today.year - self.date_of_birth.year
        if (today.month, today.day) < (
            self.date_of_birth.month,
            self.date_of_birth.day,
        ):
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
            bytes: lambda v: None,  # Don't include photo in JSON
        }


class NHSOData(BaseModel):
    """Model representing NHSO (National Health Security Office) data from Thai ID Card."""

    main_inscl: str = Field(..., description="Main insurance classification")
    sub_inscl: str = Field(..., description="Sub insurance classification")
    main_hospital_name: str = Field(..., description="Main hospital name")
    sub_hospital_name: str = Field(..., description="Sub hospital name")
    paid_type: str = Field(..., description="Payment type code")
    issue_date: date = Field(..., description="NHSO registration issue date")
    expire_date: date = Field(..., description="NHSO registration expiry date")
    update_date: date = Field(..., description="Last update date")
    change_hospital_amount: str = Field(..., description="Number of hospital changes")

    @field_validator("issue_date", "expire_date", "update_date", mode="before")
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
    def is_expired(self) -> bool:
        """Check if the NHSO registration has expired."""
        return date.today() > self.expire_date

    @computed_field
    @property
    def days_until_expiry(self) -> int:
        """Calculate days until NHSO registration expiry."""
        return (self.expire_date - date.today()).days

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            date: lambda v: v.isoformat(),
        }


class CardReaderInfo(BaseModel):
    """Information about a smart card reader."""

    index: int = Field(..., description="Reader index in the system")
    name: str = Field(..., description="Reader name/model")
    atr: Optional[str] = Field(None, description="Answer to Reset (ATR) hex string")
    connected: bool = Field(False, description="Whether a card is connected")
