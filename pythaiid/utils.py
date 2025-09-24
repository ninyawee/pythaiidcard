"""Utility functions for Thai ID Card operations."""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def thai_to_unicode(data: bytes | List[int]) -> str:
    """Convert Thai TIS-620 encoded data to Unicode string.
    
    Args:
        data: Bytes or list of integers in TIS-620 encoding
        
    Returns:
        Decoded Unicode string with # replaced by spaces and trimmed
    """
    try:
        if isinstance(data, list):
            data = bytes(data)
        
        # Decode from TIS-620 (Thai encoding)
        result = data.decode('tis-620', errors='ignore')
        
        # Replace # with space and strip whitespace
        result = result.replace("#", " ").strip()
        
        return result
    except Exception as e:
        logger.error(f"Error decoding Thai data: {e}")
        return ""


def format_cid(cid: str) -> str:
    """Format citizen ID with dashes for readability.
    
    Args:
        cid: 13-digit citizen ID
        
    Returns:
        Formatted CID (e.g., 1-2345-67890-12-3)
    """
    if len(cid) != 13:
        return cid
    
    return f"{cid[0]}-{cid[1:5]}-{cid[5:10]}-{cid[10:12]}-{cid[12]}"


def validate_cid(cid: str) -> bool:
    """Validate Thai citizen ID with checksum.
    
    Args:
        cid: 13-digit citizen ID
        
    Returns:
        True if valid, False otherwise
    """
    if not cid.isdigit() or len(cid) != 13:
        return False
    
    # Calculate checksum (Thai ID card algorithm)
    checksum = 0
    for i in range(12):
        checksum += int(cid[i]) * (13 - i)
    checksum = (11 - (checksum % 11)) % 10
    
    return checksum == int(cid[12])


def bytes_to_hex(data: bytes | List[int]) -> str:
    """Convert bytes to hex string representation.
    
    Args:
        data: Bytes or list of integers
        
    Returns:
        Hex string with spaces between bytes
    """
    if isinstance(data, list):
        data = bytes(data)
    
    return ' '.join(f'{b:02X}' for b in data)


def parse_buddhist_date(date_str: str) -> str:
    """Parse Buddhist Era date string to Gregorian.
    
    Args:
        date_str: Date in YYYYMMDD format (Buddhist Era)
        
    Returns:
        Date in YYYY-MM-DD format (Gregorian)
    """
    if not date_str or len(date_str) != 8:
        return date_str
    
    try:
        # Convert Buddhist year to Gregorian
        year = int(date_str[:4]) - 543
        month = date_str[4:6]
        day = date_str[6:8]
        
        return f"{year:04d}-{month}-{day}"
    except (ValueError, IndexError):
        return date_str


def format_address(address: str) -> str:
    """Format address for better readability.
    
    Args:
        address: Raw address string
        
    Returns:
        Formatted address with proper spacing
    """
    # Remove excessive spaces
    address = ' '.join(address.split())
    
    # Common Thai address keywords to add line breaks after
    keywords = ['หมู่ที่', 'ตำบล', 'อำเภอ', 'จังหวัด']
    
    for keyword in keywords:
        if keyword in address:
            address = address.replace(keyword, f"\n{keyword}")
    
    return address.strip()


def calculate_age(birth_date_str: str) -> Optional[int]:
    """Calculate age from Buddhist Era birth date.
    
    Args:
        birth_date_str: Birth date in YYYYMMDD format (Buddhist Era)
        
    Returns:
        Age in years, or None if invalid date
    """
    from datetime import date
    
    if not birth_date_str or len(birth_date_str) != 8:
        return None
    
    try:
        # Convert Buddhist year to Gregorian
        year = int(birth_date_str[:4]) - 543
        month = int(birth_date_str[4:6])
        day = int(birth_date_str[6:8])
        
        birth_date = date(year, month, day)
        today = date.today()
        
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
            
        return age
    except (ValueError, IndexError):
        return None


def is_card_expired(expire_date_str: str) -> bool:
    """Check if card has expired based on Buddhist Era date.
    
    Args:
        expire_date_str: Expiry date in YYYYMMDD format (Buddhist Era)
        
    Returns:
        True if expired, False otherwise
    """
    from datetime import date
    
    if not expire_date_str or len(expire_date_str) != 8:
        return False
    
    try:
        # Convert Buddhist year to Gregorian
        year = int(expire_date_str[:4]) - 543
        month = int(expire_date_str[4:6])
        day = int(expire_date_str[6:8])
        
        expire_date = date(year, month, day)
        return date.today() > expire_date
    except (ValueError, IndexError):
        return False