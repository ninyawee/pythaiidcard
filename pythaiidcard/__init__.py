"""Thai National ID Card Reader Library.

A Python library for reading data from Thai National ID cards using smart card readers.
"""

__version__ = "0.2.0"

from .exceptions import (
    CardConnectionError,
    CardTimeoutError,
    CommandError,
    DataReadError,
    InvalidCardError,
    InvalidReaderIndexError,
    NoCardDetectedError,
    NoReaderFoundError,
    SystemDependencyError,
    ThaiIDCardException,
)
from .models import Address, CardReaderInfo, Name, NHSOData, ThaiIDCard
from .reader import ThaiIDCardReader, read_thai_id_card
from .utils import (
    calculate_age,
    format_address,
    format_cid,
    is_card_expired,
    parse_buddhist_date,
    thai_to_unicode,
    validate_cid,
)

__all__ = [
    # Main classes
    "ThaiIDCardReader",
    "ThaiIDCard",
    "NHSOData",
    "CardReaderInfo",
    # Data models
    "Name",
    "Address",
    # Convenience functions
    "read_thai_id_card",
    # Utilities
    "format_cid",
    "validate_cid",
    "thai_to_unicode",
    "parse_buddhist_date",
    "format_address",
    "calculate_age",
    "is_card_expired",
    # Exceptions
    "ThaiIDCardException",
    "NoReaderFoundError",
    "NoCardDetectedError",
    "CardConnectionError",
    "InvalidCardError",
    "CommandError",
    "DataReadError",
    "InvalidReaderIndexError",
    "CardTimeoutError",
    "SystemDependencyError",
]
