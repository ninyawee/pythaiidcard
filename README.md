# pythaiid

Python library for reading Thai national ID cards using smartcard readers.

![Screen Shot 2564-10-12 at 14 24 19](https://user-images.githubusercontent.com/13503510/136910757-c00cc26e-3fe7-42dd-b277-684bc9518d11.png)

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

- **pyscard** (>=2.3.0) - Python smartcard library for PC/SC interface
- **Pillow** (>=11.3.0) - Python imaging library for photo handling

## Troubleshooting

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

## License

See LICENSE file for details.
