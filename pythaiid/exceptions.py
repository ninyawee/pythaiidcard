"""Custom exceptions for Thai ID Card operations."""


class ThaiIDCardException(Exception):
    """Base exception for Thai ID Card operations."""
    pass


class NoReaderFoundError(ThaiIDCardException):
    """Raised when no smart card reader is detected."""
    
    def __init__(self, message: str = "No smart card reader found. Please connect a reader."):
        super().__init__(message)


class NoCardDetectedError(ThaiIDCardException):
    """Raised when no card is inserted in the reader."""
    
    def __init__(self, message: str = "No card detected. Please insert a Thai ID card."):
        super().__init__(message)


class CardConnectionError(ThaiIDCardException):
    """Raised when connection to the card fails."""
    
    def __init__(self, message: str = "Failed to connect to the card.", error: Exception = None):
        if error:
            message = f"{message} Error: {error}"
        super().__init__(message)
        self.original_error = error


class InvalidCardError(ThaiIDCardException):
    """Raised when the card is not a valid Thai ID card."""
    
    def __init__(self, message: str = "The card is not a valid Thai National ID card."):
        super().__init__(message)


class CommandError(ThaiIDCardException):
    """Raised when an APDU command fails."""
    
    def __init__(self, command: str, sw1: int, sw2: int):
        self.command = command
        self.sw1 = sw1
        self.sw2 = sw2
        message = f"Command '{command}' failed with status: {sw1:02X} {sw2:02X}"
        super().__init__(message)


class DataReadError(ThaiIDCardException):
    """Raised when reading data from the card fails."""
    
    def __init__(self, field: str, error: Exception = None):
        self.field = field
        self.original_error = error
        message = f"Failed to read {field} from card"
        if error:
            message = f"{message}: {error}"
        super().__init__(message)


class InvalidReaderIndexError(ThaiIDCardException):
    """Raised when an invalid reader index is specified."""
    
    def __init__(self, index: int, available: int):
        self.index = index
        self.available = available
        message = f"Invalid reader index {index}. Available readers: 0-{available-1}"
        super().__init__(message)


class CardTimeoutError(ThaiIDCardException):
    """Raised when card operation times out."""
    
    def __init__(self, operation: str = "Card operation"):
        message = f"{operation} timed out. Please check the card is properly inserted."
        super().__init__(message)