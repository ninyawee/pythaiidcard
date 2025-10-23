# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`pythaiid` is a Python library for reading Thai National ID cards using PC/SC smartcard readers. It extracts personal information, photos, and validates data from Thai citizen ID cards.

## Development Commands

### Environment Setup
```bash
# Install system dependencies (Linux only - requires pcscd, libpcsclite-dev, swig)
mise run install-deps

# Install Python dependencies
uv sync --group dev

# For development with Streamlit interfaces
uv sync --group dev
```

### Running the Application
```bash
# Legacy CLI script
uv run python thai-idcard.py
# or
mise run run

# Modern Streamlit interfaces
uv run streamlit run debug/app_compact.py    # Compact modern UI
uv run streamlit run debug/app.py             # Full debug UI with logs
```

### Code Quality
```bash
# Lint with ruff
uv run ruff check .

# Format with ruff
uv run ruff format .
```

## Architecture

### APDU Command Flow

Thai ID cards use ISO 7816-4 APDU commands over PC/SC. The critical flow:

1. **Card Selection**: Send `SELECT APPLET` command with Thai ID applet identifier `A0 00 00 00 54 48 00 01`
2. **Response Handling**: Accept both `90 00` (success) and `61 XX` (success with more data) as valid responses
3. **Data Reading**: Each field requires two commands:
   - Initial command (e.g., `80 B0 00 04 02 00 0D` for CID)
   - GET RESPONSE command determined by ATR: `00 C0 00 00` (standard) or `00 C0 00 01` (for ATR starting with `3B 67`)

### Core Components

**`pythaiid/reader.py`** - Main reader implementation
- `ThaiIDCardReader`: Manages connection, reading operations
- Key methods:
  - `list_readers()`: Static method to enumerate available readers
  - `connect()`: Establishes connection and selects Thai ID applet
  - `read_card()`: Reads all data fields, optionally including photo (20-part JPEG)
  - `card_session()`: Context manager for automatic connect/disconnect

**`pythaiid/constants.py`** - APDU commands and status codes
- `CardCommands`: All APDU command definitions
- `ResponseStatus`: Status code validation
  - **Important**: `is_success()` accepts both `90 00` AND `61 XX` responses
- Photo reading: 20 separate 255-byte chunks (`CMD_PHOTO1` through `CMD_PHOTO20`)

**`pythaiid/models.py`** - Pydantic data models
- `ThaiIDCard`: Main card data model with validation
  - CID checksum validation (mod-11 algorithm)
  - Buddhist Era to Gregorian date conversion (subtract 543 years)
  - Computed fields: `age`, `gender_text`, `is_expired`, `days_until_expiry`
- `CardReaderInfo`: Reader enumeration data

**`pythaiid/system_check.py`** - Dependency validation
- **Smart checking**: First attempts to import `smartcard.System` (pyscard)
- If pyscard imports successfully, skip detailed system checks (dependencies are satisfied)
- Only falls back to apt package checks if pyscard import fails
- This prevents false positives when using uv-managed Python environments

**`pythaiid/exceptions.py`** - Exception hierarchy
- Base: `ThaiIDCardException`
- Common: `NoReaderFoundError`, `NoCardDetectedError`, `CardConnectionError`

### Date Handling

Thai ID cards store dates in Buddhist Era (BE) format `YYYYMMDD`:
- Buddhist Era year = Gregorian year + 543
- Example: `25380220` = February 20, 1995 (2538 - 543 = 1995)
- Conversion handled automatically in `ThaiIDCard.parse_date_field()` validator

### Photo Extraction

Photos are stored as 20 separate 255-byte chunks (5,100 bytes total JPEG):
- Read sequentially using `CMD_PHOTO1` through `CMD_PHOTO20`
- Concatenate all chunks to form complete JPEG
- Progress callbacks supported for UI feedback
- Can skip photo reading with `include_photo=False` for faster operation

## Critical Implementation Details

### Response Status Handling

**IMPORTANT**: The SELECT APPLET command returns `61 0A` (success with 10 bytes more data), NOT `90 00`. The `ResponseStatus.is_success()` method in `constants.py` accepts BOTH:
- `90 00`: Standard success
- `61 XX`: Success with more data available (XX = number of bytes)

Failing to handle `61 XX` as success causes "Failed to select Thai ID applet" errors.

### ATR-based Command Selection

Different card readers return different ATR (Answer To Reset) values:
- ATR starting with `3B 67`: Use GET RESPONSE `00 C0 00 01`
- All others: Use GET RESPONSE `00 C0 00 00`

See `CardCommands.get_read_request()` for ATR detection logic.

### System Dependency Checking

When modifying `system_check.py`:
- Always check pyscard import FIRST before checking system packages
- This prevents false positives in virtual environments
- System package checks (`apt_pkg`) only run if pyscard import fails
- Skip checks entirely with `skip_system_check=True` parameter

## Streamlit Interfaces

Two debug interfaces exist in `debug/`:

**`app_compact.py`** (Recommended)
- Modern dark theme with gradient cards
- Single-page layout with inline controls
- Production-ready appearance
- Best for end-user card reading

**`app.py`** (Debug/Development)
- Multi-tab layout with sidebar
- Comprehensive debug logging
- Reader information details
- Best for development and troubleshooting

Both use Streamlit's new `width='stretch'` parameter (not deprecated `use_container_width=True`).

## Testing Thai ID Card Reading

When testing card reading functionality:

1. **Reader Detection**: Call `ThaiIDCardReader.list_readers()` to enumerate available PC/SC readers
2. **Connection**: Verify ATR is received (format: `3B 79 96 00 00 54 48 20 4E 49 44 20 31 37` for Thai ID)
3. **Applet Selection**: Must receive `61 0A` or `90 00` response
4. **Data Reading**: Each field read should complete successfully
5. **Photo Reading**: 20 parts, can monitor progress with callback

Common test card reader: `Alcor Link AK9563`

## Package Management

- Uses `uv` for fast dependency management
- Requires Python 3.13+ (uses 3.13 for better dependency compatibility vs 3.14)
- Development dependencies include Streamlit for debug interfaces
- Build system: `hatchling` for editable installs

## Debugging Tips

When debugging card reading issues:

1. Check `pcscd` service status: `systemctl status pcscd`
2. Verify reader detection: Run `ThaiIDCardReader.list_readers()`
3. Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`
4. Use Streamlit debug interface for visual feedback
5. Check ATR value to ensure correct GET RESPONSE command
6. Verify response codes - `61 XX` is SUCCESS, not an error

## File Organization

```
pythaiid/           # Core library
├── reader.py       # Main ThaiIDCardReader class
├── models.py       # Pydantic models (ThaiIDCard, CardReaderInfo)
├── constants.py    # APDU commands, response codes
├── exceptions.py   # Exception hierarchy
├── utils.py        # Utility functions (CID validation, date parsing)
└── system_check.py # Dependency validation

debug/              # Streamlit debug interfaces
├── app.py          # Full debug UI (multi-tab)
└── app_compact.py  # Modern compact UI (single-page)
```

Core functionality is in `reader.py`, which orchestrates APDU commands from `constants.py`, validates with `models.py`, and handles errors via `exceptions.py`.
