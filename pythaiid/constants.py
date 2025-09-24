"""APDU command constants for Thai National ID Card."""

from enum import Enum
from typing import List


class APDUCommand:
    """Base class for APDU commands."""
    
    def __init__(self, command: List[int], description: str):
        self.command = command
        self.description = description
    
    def __repr__(self) -> str:
        hex_cmd = " ".join(f"{b:02X}" for b in self.command)
        return f"{self.description}: {hex_cmd}"


class CardCommands:
    """APDU commands for Thai National ID Card operations."""
    
    # Card selection
    SELECT_APPLET = APDUCommand(
        [0x00, 0xA4, 0x04, 0x00, 0x08],
        "Select Thai ID Card applet"
    )
    
    THAI_ID_APPLET = [0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01]
    
    # Personal information commands
    CID = APDUCommand(
        [0x80, 0xb0, 0x00, 0x04, 0x02, 0x00, 0x0d],
        "Citizen ID (13 digits)"
    )
    
    THAI_FULLNAME = APDUCommand(
        [0x80, 0xb0, 0x00, 0x11, 0x02, 0x00, 0x64],
        "Full name in Thai"
    )
    
    ENGLISH_FULLNAME = APDUCommand(
        [0x80, 0xb0, 0x00, 0x75, 0x02, 0x00, 0x64],
        "Full name in English"
    )
    
    DATE_OF_BIRTH = APDUCommand(
        [0x80, 0xb0, 0x00, 0xD9, 0x02, 0x00, 0x08],
        "Date of birth (YYYYMMDD in Buddhist Era)"
    )
    
    GENDER = APDUCommand(
        [0x80, 0xb0, 0x00, 0xE1, 0x02, 0x00, 0x01],
        "Gender (1=Male, 2=Female)"
    )
    
    CARD_ISSUER = APDUCommand(
        [0x80, 0xb0, 0x00, 0xF6, 0x02, 0x00, 0x64],
        "Card issuing organization"
    )
    
    ISSUE_DATE = APDUCommand(
        [0x80, 0xb0, 0x01, 0x67, 0x02, 0x00, 0x08],
        "Card issue date (YYYYMMDD in Buddhist Era)"
    )
    
    EXPIRE_DATE = APDUCommand(
        [0x80, 0xb0, 0x01, 0x6F, 0x02, 0x00, 0x08],
        "Card expiry date (YYYYMMDD in Buddhist Era)"
    )
    
    ADDRESS = APDUCommand(
        [0x80, 0xb0, 0x15, 0x79, 0x02, 0x00, 0x64],
        "Registered address"
    )
    
    # Photo commands (20 parts)
    PHOTO_COMMANDS = [
        APDUCommand([0x80, 0xb0, 0x01, 0x7B, 0x02, 0x00, 0xFF], "Photo part 1/20"),
        APDUCommand([0x80, 0xb0, 0x02, 0x7A, 0x02, 0x00, 0xFF], "Photo part 2/20"),
        APDUCommand([0x80, 0xb0, 0x03, 0x79, 0x02, 0x00, 0xFF], "Photo part 3/20"),
        APDUCommand([0x80, 0xb0, 0x04, 0x78, 0x02, 0x00, 0xFF], "Photo part 4/20"),
        APDUCommand([0x80, 0xb0, 0x05, 0x77, 0x02, 0x00, 0xFF], "Photo part 5/20"),
        APDUCommand([0x80, 0xb0, 0x06, 0x76, 0x02, 0x00, 0xFF], "Photo part 6/20"),
        APDUCommand([0x80, 0xb0, 0x07, 0x75, 0x02, 0x00, 0xFF], "Photo part 7/20"),
        APDUCommand([0x80, 0xb0, 0x08, 0x74, 0x02, 0x00, 0xFF], "Photo part 8/20"),
        APDUCommand([0x80, 0xb0, 0x09, 0x73, 0x02, 0x00, 0xFF], "Photo part 9/20"),
        APDUCommand([0x80, 0xb0, 0x0A, 0x72, 0x02, 0x00, 0xFF], "Photo part 10/20"),
        APDUCommand([0x80, 0xb0, 0x0B, 0x71, 0x02, 0x00, 0xFF], "Photo part 11/20"),
        APDUCommand([0x80, 0xb0, 0x0C, 0x70, 0x02, 0x00, 0xFF], "Photo part 12/20"),
        APDUCommand([0x80, 0xb0, 0x0D, 0x6F, 0x02, 0x00, 0xFF], "Photo part 13/20"),
        APDUCommand([0x80, 0xb0, 0x0E, 0x6E, 0x02, 0x00, 0xFF], "Photo part 14/20"),
        APDUCommand([0x80, 0xb0, 0x0F, 0x6D, 0x02, 0x00, 0xFF], "Photo part 15/20"),
        APDUCommand([0x80, 0xb0, 0x10, 0x6C, 0x02, 0x00, 0xFF], "Photo part 16/20"),
        APDUCommand([0x80, 0xb0, 0x11, 0x6B, 0x02, 0x00, 0xFF], "Photo part 17/20"),
        APDUCommand([0x80, 0xb0, 0x12, 0x6A, 0x02, 0x00, 0xFF], "Photo part 18/20"),
        APDUCommand([0x80, 0xb0, 0x13, 0x69, 0x02, 0x00, 0xFF], "Photo part 19/20"),
        APDUCommand([0x80, 0xb0, 0x14, 0x68, 0x02, 0x00, 0xFF], "Photo part 20/20"),
    ]
    
    @classmethod
    def get_read_request(cls, atr: List[int]) -> List[int]:
        """Get the appropriate read request based on ATR.
        
        Args:
            atr: Answer to Reset bytes
            
        Returns:
            Read request command bytes
        """
        if len(atr) >= 2 and atr[0] == 0x3B and atr[1] == 0x67:
            return [0x00, 0xc0, 0x00, 0x01]
        else:
            return [0x00, 0xc0, 0x00, 0x00]


class ResponseStatus(Enum):
    """Smart card response status codes."""
    
    SUCCESS = (0x90, 0x00)
    MORE_DATA = (0x61, None)  # SW2 contains the length
    WRONG_LENGTH = (0x6C, None)  # SW2 contains correct length
    COMMAND_NOT_ALLOWED = (0x69, 0x86)
    WRONG_PARAMETERS = (0x6A, 0x86)
    FILE_NOT_FOUND = (0x6A, 0x82)
    
    @classmethod
    def is_success(cls, sw1: int, sw2: int) -> bool:
        """Check if response indicates success."""
        return sw1 == 0x90 and sw2 == 0x00
    
    @classmethod
    def has_more_data(cls, sw1: int) -> bool:
        """Check if more data is available."""
        return sw1 == 0x61