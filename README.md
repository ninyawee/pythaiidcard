# pythaiidcard

Python library for reading Thai national ID cards using smartcard readers.

![pythaiidcard Cover](https://raw.githubusercontent.com/ninyawee/pythaiidcard/master/docs/assets/pythaiidcard-cover.png)

![Thai ID Card Reader Demo](https://raw.githubusercontent.com/ninyawee/pythaiidcard/master/docs/assets/debug%20interface.png)

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Flutter Library Development](#flutter-library-development)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Command Line](#command-line)
  - [Web Interface](#web-interface-streamlit)
  - [Python Library](#python-library)
- [Data Fields](#data-fields)
- [Dependencies](#dependencies)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Credits](#credits)
- [License](#license)

## Features

- ✅ **Full Card Data Extraction**: Read all information from Thai ID cards
- 📸 **Photo Support**: Extract and save card photos (JPEG format)
- 🔒 **Data Validation**: Automatic CID checksum validation and date parsing
- 📅 **Date Conversion**: Buddhist Era to Gregorian calendar conversion
- 🎨 **Modern Web UI**: Streamlit-based debug interfaces
- 🐍 **Type-Safe**: Full type hints and Pydantic models
- 🔍 **Error Handling**: Comprehensive exception handling and system checks
- 📦 **Zero Config**: Auto-detects readers and connects to cards
- 🚀 **Fast**: Efficient APDU command implementation

## Quick Start

```bash
# 1. Install system dependencies
sudo apt-get install -y pcscd libpcsclite-dev python3-dev swig

# 2. Install Python dependencies
uv sync --group dev

# 3. Run the web interface
uv run streamlit run debug/app_compact.py
```

Then open http://localhost:8501 in your browser, insert your Thai ID card, and click "Scan Readers" → "Connect" → "Read Card".

## Flutter Library Development

We are actively working on a **Flutter version** of this library for cross-platform mobile support (iOS/Android). The development is in progress at [`playground/thai_idcard_reader_test/`](playground/thai_idcard_reader_test/).

### Key Features
- **Package:** Uses the [`ccid`](https://pub.dev/packages/ccid) Flutter package for smartcard reading
- **Platform Support:** iOS (13.0+) and Android with USB OTG smartcard readers
- **Architecture:** Mirrors the Python implementation using APDU commands over PC/SC
- **CI/CD:** Automated iOS builds via GitHub Actions and Fastlane

### Getting Started with Flutter Version

```bash
cd playground/thai_idcard_reader_test/

# Install dependencies
flutter pub get

# Run on Android device
flutter run

# For iOS builds, see the CI/CD workflow or use GitHub Actions
```

See the [Flutter project README](playground/thai_idcard_reader_test/README.md) for detailed setup instructions, hardware requirements, and iOS cloud build configuration.

**Note:** Thai National ID cards do NOT support NFC - external USB OTG (Android) or MFi-certified (iOS) smartcard readers are required.

**iOS Testing Limitation:** The author currently lacks access to a Mac, making iOS testing challenging. However, the project includes GitHub Actions CI/CD for automated iOS builds. Community contributions and testing on iOS devices are highly appreciated!

## Credits

This project is inspired by and based on:
- [Thai National ID Card Reader Gist](https://gist.github.com/bouroo/8b34daf5b7deed57ea54819ff7aeef6e) by bouroo
- [lab-python3-th-idcard](https://github.com/pstudiodev1/lab-python3-th-idcard) by pstudiodev1

## Prerequisites

### System Dependencies

This project requires the following system packages:

- `pcscd` - PC/SC Smart Card Daemon
- `libpcsclite-dev` - PC/SC development files
- `python3-dev` - Python development headers
- `swig` - Interface compiler for Python bindings

Install them using:

```bash
sudo apt-get update
sudo apt-get install -y pcscd libpcsclite-dev python3-dev swig
```

Or if you have `mise` installed:

```bash
mise run install-deps
```

## Installation

This project uses `uv` for Python package management.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv sync
```

Or with mise:

```bash
mise run setup
```

## Usage

### Command Line

Connect your smartcard reader and insert a Thai ID card, then run:

```bash
uv run python thai-idcard.py
```

Or:

```bash
mise run run
```

The script will:
- Detect available smartcard readers
- Connect to the first reader automatically
- Read personal data from the Thai ID card including:
  - Citizen ID
  - Thai/English full name
  - Date of birth
  - Gender
  - Card issuer
  - Issue/Expiry dates
  - Address
  - Photo (saved as `{CID}.jpg`)

### Web Interface (Streamlit)

For a modern web-based interface with visual feedback:

```bash
# Compact modern interface (recommended)
uv run streamlit run debug/app_compact.py

# Full debug interface with logs
uv run streamlit run debug/app.py
```

Features:
- 🔍 Visual reader detection and selection
- 🔌 Connection status monitoring
- 📖 Interactive card reading with progress bars
- 📸 Photo preview and download
- 💾 Export data as JSON, CSV, or photo
- 🐛 Real-time debug logging (full interface)

See [debug/README.md](debug/README.md) for detailed documentation.

### Python Library

```python
from pythaiidcard import ThaiIDCardReader

# Basic usage - auto-connect and read card
reader = ThaiIDCardReader()
with reader.card_session():
    card = reader.read_card(include_photo=True)

    print(f"Name: {card.english_fullname}")
    print(f"CID: {card.cid}")
    print(f"Age: {card.age}")
    print(f"Expires: {card.expire_date}")
    print(f"Valid: {not card.is_expired}")

    # Save photo
    if card.photo:
        card.save_photo()  # Saves as {cid}.jpg

# Advanced usage - manual control
from pythaiidcard.reader import ThaiIDCardReader

# List available readers
readers = ThaiIDCardReader.list_readers()
for reader_info in readers:
    print(f"Reader {reader_info.index}: {reader_info.name}")
    print(f"  ATR: {reader_info.atr}")
    print(f"  Connected: {reader_info.connected}")

# Connect to specific reader
reader = ThaiIDCardReader(reader_index=0)
reader.connect()

# Read without photo for faster operation
card = reader.read_card(include_photo=False)

# Read with progress callback
def on_photo_progress(current, total):
    print(f"Reading photo: {current}/{total}")

card = reader.read_card(
    include_photo=True,
    photo_progress_callback=on_photo_progress
)

reader.disconnect()

# Access card data
print(f"Thai Name: {card.thai_fullname}")
print(f"English Name: {card.english_fullname}")
print(f"Gender: {card.gender_text}")  # "Male" or "Female"
print(f"Address: {card.address}")
print(f"Issue Date: {card.issue_date}")
print(f"Days until expiry: {card.days_until_expiry}")

# Export as JSON
import json
card_json = card.model_dump_json(indent=2)
print(card_json)
```

## Data Fields

The following information is extracted from the card:

| Field | Description |
|-------|-------------|
| CID | 13-digit citizen identification number |
| TH Fullname | Full name in Thai |
| EN Fullname | Full name in English |
| Date of birth | Birth date |
| Gender | Gender |
| Card Issuer | Issuing organization |
| Issue Date | Card issue date |
| Expire Date | Card expiration date |
| Address | Registered address |
| Photo | JPEG photo (saved to file) |

## Dependencies

### Python Packages

- **pyscard** (>=2.3.0) - Python smartcard library for PC/SC interface
- **Pillow** (>=11.3.0) - Python imaging library for photo handling
- **pydantic** (>=2.0) - Data validation and settings management
- **python-dateutil** (>=2.8.2) - Date parsing utilities

### Development Dependencies

- **streamlit** (>=1.28.0) - Web interface framework (optional)
- **ruff** (>=0.8.4) - Linting and formatting

## Troubleshooting

### SystemDependencyError: Missing required system dependencies

The library will automatically check for required system dependencies on Linux systems with apt package manager. If dependencies are missing, you'll see a helpful error message with installation instructions.

Example error:
```
SystemDependencyError: Missing required system dependencies:

  ✗ PC/SC Smart Card Daemon (pcscd)
  ✗ PC/SC Lite development library (libpcsclite-dev)

To install missing dependencies, run:

  sudo apt-get update && sudo apt-get install -y pcscd libpcsclite-dev python3-dev swig
```

**To skip the dependency check** (if you know dependencies are installed via other means):
```python
from pythaiidcard import ThaiIDCardReader

reader = ThaiIDCardReader(skip_system_check=True)
```

### "No such file or directory: winscard.h"
Install the system dependencies listed above, particularly `libpcsclite-dev`.

### "No readers available"
- Ensure your smartcard reader is connected
- Check that the `pcscd` service is running: `sudo systemctl status pcscd`
- Start it if needed: `sudo systemctl start pcscd`

### Permission denied
Add your user to the `scard` group:
```bash
sudo usermod -a -G scard $USER
```
Then log out and log back in.

## Project Structure

```
pythaiidcard/
├── pythaiidcard/              # Main library package
│   ├── __init__.py       # Package initialization
│   ├── reader.py         # ThaiIDCardReader implementation
│   ├── models.py         # Pydantic data models
│   ├── constants.py      # APDU commands and response codes
│   ├── exceptions.py     # Custom exceptions
│   ├── utils.py          # Utility functions
│   └── system_check.py   # System dependency checking
├── debug/                # Debug interfaces
│   ├── app.py           # Full debug interface (multi-tab)
│   ├── app_compact.py   # Modern compact interface
│   ├── README.md        # Debug interface documentation
│   └── RUN_COMPACT.sh   # Quick launch script
├── thai-idcard.py       # Legacy CLI script
├── pyproject.toml       # Project configuration
└── README.md            # This file
```

### Key Components

- **ThaiIDCardReader**: Main class for reading Thai ID cards
- **ThaiIDCard**: Pydantic model with validated card data
- **CardReaderInfo**: Information about available card readers
- **System Check**: Automatic validation of system dependencies
- **Debug Interfaces**: Streamlit-based web UIs for testing and debugging

## License

See LICENSE file for details.
