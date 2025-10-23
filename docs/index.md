# pythaiidcard

**Python library for reading Thai national ID cards using smartcard readers**

[![License](https://img.shields.io/badge/license-ISC-blue.svg)](https://github.com/ninyawee/pythaiidcard/blob/master/LICENSE)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

![pythaiidcard Cover](assets/pythaiidcard-cover.png)

![Thai ID Card Reader Demo](<assets/debug interface.png>)

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
# 1. Install system dependencies (Linux only)
sudo apt-get install -y pcscd libpcsclite-dev python3-dev swig

# 2. Install pythaiidcard
pip install pythaiidcard

# 3. Use in your Python code
python
>>> from pythaiidcard import ThaiIDCardReader
>>> reader = ThaiIDCardReader()
>>> with reader.card_session():
...     card = reader.read_card()
...     print(f"Name: {card.english_fullname}")
...     print(f"CID: {card.cid}")
```

## What Can You Read?

The library extracts the following information from Thai National ID cards:

| Field | Description |
|-------|-------------|
| CID | 13-digit citizen identification number |
| Thai Name | Full name in Thai script |
| English Name | Full name in English |
| Date of Birth | Birth date with age calculation |
| Gender | Gender (Male/Female) |
| Address | Registered address |
| Card Issuer | Issuing organization |
| Issue Date | Card issue date |
| Expire Date | Card expiration date |
| Photo | JPEG photo (saved to file) |

## System Requirements

### Hardware
- **Smartcard Reader**: PC/SC compatible smartcard reader
  - Recommended: [USB-C Smart Card Reader](https://s.shopee.co.th/9zpLTwW3c8)* (tested by author)
  - Or any other PC/SC compatible reader
- **Thai National ID card**: Modern card with chip (issued 2010+)

<small>* Affiliate link</small>

### Software
- Python 3.13 or higher
- Linux (tested on Ubuntu/Debian)
- Required system packages (see [Installation](installation.md))

## Use Cases

- **Identity Verification**: Build KYC (Know Your Customer) systems
- **Government Services**: Integrate with e-government applications
- **Access Control**: Create ID-based access control systems
- **Data Entry**: Automate data entry from ID cards
- **Age Verification**: Verify age for age-restricted services

## Credits

This project is inspired by and based on:

- [Thai National ID Card Reader Gist](https://gist.github.com/bouroo/8b34daf5b7deed57ea54819ff7aeef6e) by bouroo
- [lab-python3-th-idcard](https://github.com/pstudiodev1/lab-python3-th-idcard) by pstudiodev1

## License

This project is licensed under the ISC License. See the [LICENSE](https://github.com/ninyawee/pythaiidcard/blob/master/LICENSE) file for details.

## Next Steps

- [Installation Guide →](installation.md)
- [Usage Examples →](usage.md)
- [API Reference →](api-reference.md)
- [Troubleshooting →](troubleshooting.md)
