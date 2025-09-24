"""Thai ID Card reader implementation."""

import logging
from contextlib import contextmanager
from typing import List, Optional, Tuple, Generator

from smartcard.CardConnection import CardConnection
from smartcard.System import readers
from smartcard.util import toHexString

from .constants import APDUCommand, CardCommands, ResponseStatus
from .exceptions import (
    CardConnectionError,
    CommandError,
    DataReadError,
    InvalidCardError,
    InvalidReaderIndexError,
    NoCardDetectedError,
    NoReaderFoundError,
)
from .models import CardReaderInfo, ThaiIDCard
from .utils import thai_to_unicode

logger = logging.getLogger(__name__)


class ThaiIDCardReader:
    """Reader for Thai National ID Cards."""
    
    def __init__(self, reader_index: Optional[int] = None, retry_count: int = 3):
        """Initialize the Thai ID Card reader.
        
        Args:
            reader_index: Index of the reader to use (None for auto-select)
            retry_count: Number of retries for failed operations
        """
        self.reader_index = reader_index
        self.retry_count = retry_count
        self.connection: Optional[CardConnection] = None
        self.atr: Optional[List[int]] = None
        self._request_command: Optional[List[int]] = None
    
    @staticmethod
    def list_readers() -> List[CardReaderInfo]:
        """List all available smart card readers.
        
        Returns:
            List of CardReaderInfo objects
            
        Raises:
            NoReaderFoundError: If no readers are found
        """
        reader_list = readers()
        
        if not reader_list:
            raise NoReaderFoundError()
        
        readers_info = []
        for index, reader in enumerate(reader_list):
            info = CardReaderInfo(
                index=index,
                name=str(reader),
                connected=False
            )
            
            # Try to get ATR if card is present
            try:
                connection = reader.createConnection()
                connection.connect()
                atr = connection.getATR()
                info.atr = toHexString(atr)
                info.connected = True
                connection.disconnect()
            except Exception:
                pass
            
            readers_info.append(info)
        
        return readers_info
    
    def _get_reader(self) -> 'smartcard.reader.Reader':
        """Get the smart card reader.
        
        Returns:
            Selected reader instance
            
        Raises:
            NoReaderFoundError: If no readers are found
            InvalidReaderIndexError: If specified index is invalid
        """
        reader_list = readers()
        
        if not reader_list:
            raise NoReaderFoundError()
        
        if self.reader_index is None:
            # Auto-select first reader
            logger.info(f"Auto-selecting first reader: {reader_list[0]}")
            return reader_list[0]
        
        if self.reader_index < 0 or self.reader_index >= len(reader_list):
            raise InvalidReaderIndexError(self.reader_index, len(reader_list))
        
        logger.info(f"Using reader {self.reader_index}: {reader_list[self.reader_index]}")
        return reader_list[self.reader_index]
    
    def connect(self) -> None:
        """Connect to the Thai ID card.
        
        Raises:
            NoCardDetectedError: If no card is detected
            CardConnectionError: If connection fails
            InvalidCardError: If card is not a Thai ID card
        """
        try:
            reader = self._get_reader()
            self.connection = reader.createConnection()
            self.connection.connect()
            
            self.atr = self.connection.getATR()
            logger.info(f"Connected to card, ATR: {toHexString(self.atr)}")
            
            # Determine request command based on ATR
            self._request_command = CardCommands.get_read_request(self.atr)
            
            # Select Thai ID applet
            self._select_applet()
            
        except NoReaderFoundError:
            raise
        except InvalidReaderIndexError:
            raise
        except Exception as e:
            if "No card in reader" in str(e):
                raise NoCardDetectedError()
            raise CardConnectionError(error=e)
    
    def disconnect(self) -> None:
        """Disconnect from the card."""
        if self.connection:
            try:
                self.connection.disconnect()
                logger.info("Disconnected from card")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            finally:
                self.connection = None
                self.atr = None
                self._request_command = None
    
    def _select_applet(self) -> None:
        """Select the Thai ID card applet.
        
        Raises:
            InvalidCardError: If not a Thai ID card
        """
        command = CardCommands.SELECT_APPLET.command + CardCommands.THAI_ID_APPLET
        data, sw1, sw2 = self.connection.transmit(command)
        
        if not ResponseStatus.is_success(sw1, sw2):
            raise InvalidCardError(f"Failed to select Thai ID applet: {sw1:02X} {sw2:02X}")
        
        logger.info("Thai ID applet selected successfully")
    
    def _send_command(self, apdu_command: APDUCommand) -> bytes:
        """Send an APDU command and get the response.
        
        Args:
            apdu_command: APDU command to send
            
        Returns:
            Response data as bytes
            
        Raises:
            CommandError: If command fails
        """
        if not self.connection:
            raise CardConnectionError("Not connected to card")
        
        # Send initial command
        data, sw1, sw2 = self.connection.transmit(apdu_command.command)
        
        # Get response data
        if ResponseStatus.has_more_data(sw1):
            # Read the response
            read_cmd = self._request_command + [apdu_command.command[-1]]
            data, sw1, sw2 = self.connection.transmit(read_cmd)
            
            if not ResponseStatus.is_success(sw1, sw2):
                raise CommandError(apdu_command.description, sw1, sw2)
        
        return bytes(data)
    
    def _read_text_field(self, apdu_command: APDUCommand) -> str:
        """Read a text field from the card.
        
        Args:
            apdu_command: APDU command for the field
            
        Returns:
            Decoded text string
            
        Raises:
            DataReadError: If reading fails
        """
        for attempt in range(self.retry_count):
            try:
                data = self._send_command(apdu_command)
                return thai_to_unicode(data)
            except Exception as e:
                if attempt == self.retry_count - 1:
                    raise DataReadError(apdu_command.description, e)
                logger.warning(f"Retry {attempt + 1} for {apdu_command.description}")
    
    def _read_photo(self, progress_callback: Optional[callable] = None) -> bytes:
        """Read photo data from the card.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete photo data as bytes
            
        Raises:
            DataReadError: If reading photo fails
        """
        photo_data = b''
        total_parts = len(CardCommands.PHOTO_COMMANDS)
        
        for i, photo_cmd in enumerate(CardCommands.PHOTO_COMMANDS):
            try:
                data = self._send_command(photo_cmd)
                photo_data += data
                
                if progress_callback:
                    progress_callback(i + 1, total_parts)
                    
                logger.debug(f"Read photo part {i + 1}/{total_parts}")
            except Exception as e:
                raise DataReadError(f"Photo part {i + 1}", e)
        
        return photo_data
    
    def read_card(self, include_photo: bool = True, 
                  photo_progress_callback: Optional[callable] = None) -> ThaiIDCard:
        """Read all data from Thai ID card.
        
        Args:
            include_photo: Whether to read the photo
            photo_progress_callback: Optional callback for photo reading progress
            
        Returns:
            ThaiIDCard object with all card data
            
        Raises:
            Various exceptions for connection and reading errors
        """
        if not self.connection:
            raise CardConnectionError("Not connected to card. Call connect() first.")
        
        logger.info("Reading Thai ID card data...")
        
        # Read all fields
        cid = self._read_text_field(CardCommands.CID)
        thai_fullname = self._read_text_field(CardCommands.THAI_FULLNAME)
        english_fullname = self._read_text_field(CardCommands.ENGLISH_FULLNAME)
        date_of_birth = self._read_text_field(CardCommands.DATE_OF_BIRTH)
        gender = self._read_text_field(CardCommands.GENDER)
        card_issuer = self._read_text_field(CardCommands.CARD_ISSUER)
        issue_date = self._read_text_field(CardCommands.ISSUE_DATE)
        expire_date = self._read_text_field(CardCommands.EXPIRE_DATE)
        address = self._read_text_field(CardCommands.ADDRESS)
        
        # Read photo if requested
        photo = None
        if include_photo:
            logger.info("Reading photo data...")
            photo = self._read_photo(photo_progress_callback)
        
        # Create and return the card model
        card = ThaiIDCard(
            cid=cid,
            thai_fullname=thai_fullname,
            english_fullname=english_fullname,
            date_of_birth=date_of_birth,
            gender=gender,
            card_issuer=card_issuer,
            issue_date=issue_date,
            expire_date=expire_date,
            address=address,
            photo=photo
        )
        
        logger.info(f"Successfully read card for CID: {cid}")
        return card
    
    @contextmanager
    def card_session(self) -> Generator['ThaiIDCardReader', None, None]:
        """Context manager for card operations.
        
        Usage:
            with reader.card_session():
                card = reader.read_card()
        """
        try:
            self.connect()
            yield self
        finally:
            self.disconnect()


def read_thai_id_card(reader_index: Optional[int] = None,
                     include_photo: bool = True) -> ThaiIDCard:
    """Convenience function to read a Thai ID card.
    
    Args:
        reader_index: Reader index to use (None for auto-select)
        include_photo: Whether to include photo data
        
    Returns:
        ThaiIDCard object with card data
        
    Raises:
        Various exceptions for errors
    """
    reader = ThaiIDCardReader(reader_index)
    
    with reader.card_session():
        return reader.read_card(include_photo)