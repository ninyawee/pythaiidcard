# Usage Guide

## Basic Usage

### Quick Read

The simplest way to read a Thai ID card:

```python
from pythaiid import read_thai_id_card

# Auto-connect and read the card
card = read_thai_id_card()

print(f"Name: {card.english_fullname}")
print(f"CID: {card.cid}")
print(f"Age: {card.age}")
```

### Using Context Manager

For better resource management:

```python
from pythaiid import ThaiIDCardReader

reader = ThaiIDCardReader()

with reader.card_session():
    card = reader.read_card(include_photo=True)

    print(f"Thai Name: {card.thai_fullname}")
    print(f"English Name: {card.english_fullname}")
    print(f"Gender: {card.gender_text}")
    print(f"Valid: {not card.is_expired}")

    # Save photo
    if card.photo:
        photo_path = card.save_photo()
        print(f"Photo saved: {photo_path}")
```

## Advanced Usage

### Manual Connection Control

```python
from pythaiid import ThaiIDCardReader

# List available readers
readers = ThaiIDCardReader.list_readers()
for reader_info in readers:
    print(f"Reader {reader_info.index}: {reader_info.name}")
    print(f"  ATR: {reader_info.atr}")
    print(f"  Status: {'Card Present' if reader_info.connected else 'No Card'}")

# Connect to specific reader
reader = ThaiIDCardReader(reader_index=0)
reader.connect()

# Read card data
card = reader.read_card(include_photo=False)

# Disconnect when done
reader.disconnect()
```

### Reading Without Photo

For faster operation, skip the photo:

```python
card = reader.read_card(include_photo=False)
```

Photo reading takes approximately 2-3 seconds, while reading text data is nearly instantaneous.

### Photo Progress Callback

Monitor photo reading progress:

```python
def on_photo_progress(current, total):
    percentage = (current / total) * 100
    print(f"Reading photo: {percentage:.0f}% ({current}/{total})")

card = reader.read_card(
    include_photo=True,
    photo_progress_callback=on_photo_progress
)
```

## Working with Card Data

### Accessing Fields

```python
# Basic information
print(f"CID: {card.cid}")
print(f"Thai Name: {card.thai_fullname}")
print(f"English Name: {card.english_fullname}")

# Dates
print(f"Date of Birth: {card.date_of_birth}")  # datetime object
print(f"Age: {card.age}")
print(f"Issue Date: {card.issue_date}")
print(f"Expire Date: {card.expire_date}")

# Status
print(f"Days until expiry: {card.days_until_expiry}")
print(f"Is expired: {card.is_expired}")

# Gender
print(f"Gender Code: {card.gender}")  # "1" or "2"
print(f"Gender: {card.gender_text}")  # "Male" or "Female"

# Address
print(f"Address: {card.address}")

# Card issuer
print(f"Issued by: {card.card_issuer}")
```

### Saving Photo

```python
# Save with default name ({cid}.jpg)
if card.photo:
    photo_path = card.save_photo()
    print(f"Saved to: {photo_path}")

# Save with custom path
photo_path = card.save_photo("/path/to/photos/my_photo.jpg")
```

### Exporting Data

#### As JSON

```python
import json

# Export to JSON string
json_data = card.model_dump_json(indent=2)
print(json_data)

# Export to dict (exclude photo binary data)
data_dict = card.model_dump(exclude={"photo"})
print(json.dumps(data_dict, ensure_ascii=False, indent=2, default=str))
```

#### As Dict

```python
# Get all data as dictionary
data = card.model_dump()

# Exclude certain fields
data = card.model_dump(exclude={"photo"})

# Include only certain fields
data = card.model_dump(include={"cid", "english_fullname", "date_of_birth"})
```

## Utility Functions

### CID Validation

```python
from pythaiid import validate_cid, format_cid

# Validate CID checksum
cid = "1234567890123"
if validate_cid(cid):
    print("Valid CID")
else:
    print("Invalid CID")

# Format CID with dashes
formatted = format_cid(cid)
print(formatted)  # "1-2345-67890-12-3"
```

### Date Utilities

```python
from pythaiid import parse_buddhist_date, calculate_age, is_card_expired
from datetime import datetime

# Parse Buddhist Era date
be_date = "25640101"  # YYYYMMDD in Buddhist Era
gregorian_date = parse_buddhist_date(be_date)

# Calculate age
age = calculate_age(datetime(1990, 1, 1))
print(f"Age: {age}")

# Check if card expired
expired = is_card_expired(datetime(2020, 1, 1))
print(f"Expired: {expired}")
```

### Thai Text Conversion

```python
from pythaiid import thai_to_unicode

# Convert Thai text from card encoding
thai_bytes = b"\xe0\xb8\x99\xe0\xb8\xb2\xe0\xb8\xa2..."
thai_text = thai_to_unicode(thai_bytes)
print(thai_text)
```

## Command-Line Interface

### List Readers

```bash
pythaiid list-readers
```

Output:
```
┏━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Index ┃ Reader Name                ┃ Status      ┃ ATR           ┃
┡━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ 0     │ Generic USB Reader         │ Card Present│ 3B 67 00...   │
└───────┴────────────────────────────┴─────────────┴───────────────┘
```

### Read Card

```bash
# Read and display card data
pythaiid read

# Read without photo
pythaiid read --no-photo

# Save photo to specific path
pythaiid read --save-photo /path/to/photo.jpg

# Use specific reader
pythaiid read --reader 0

# Output as JSON
pythaiid read --format json

# Verbose output
pythaiid read --verbose
```

### Watch for Cards

Continuously monitor for card insertions:

```bash
pythaiid watch --interval 2
```

Output:
```
Watching for Thai ID cards... Press Ctrl+C to stop.

Card detected!
CID: 1-2345-67890-12-3
Name: John Doe
Thai Name: นาย จอห์น โด

Card removed
```

### Validate CID

```bash
pythaiid validate 1234567890123
```

## Web Interface (Streamlit)

For a visual interface with real-time feedback:

```bash
# Compact modern interface (recommended)
uv run streamlit run debug/app_compact.py

# Full debug interface with logs
uv run streamlit run debug/app.py
```

Open http://localhost:8501 in your browser.

### Features

- 🔍 Visual reader detection and selection
- 🔌 Connection status monitoring
- 📖 Interactive card reading with progress bars
- 📸 Photo preview and download
- 💾 Export data as JSON, CSV, or photo
- 🐛 Real-time debug logging (full interface)

See [debug/README.md](https://github.com/ninyawee/pythaiid/blob/master/debug/README.md) for detailed documentation.

## Error Handling

### Catching Exceptions

```python
from pythaiid import (
    ThaiIDCardReader,
    NoReaderFoundError,
    NoCardDetectedError,
    CardConnectionError,
    InvalidCardError,
    SystemDependencyError,
)

try:
    reader = ThaiIDCardReader()
    with reader.card_session():
        card = reader.read_card()
        print(f"Success: {card.english_fullname}")

except SystemDependencyError as e:
    print(f"Missing system dependencies: {e}")
    print("Install: sudo apt-get install pcscd libpcsclite-dev python3-dev swig")

except NoReaderFoundError:
    print("No smartcard reader detected. Please connect a reader.")

except NoCardDetectedError:
    print("No card detected. Please insert a Thai ID card.")

except InvalidCardError:
    print("The inserted card is not a valid Thai ID card.")

except CardConnectionError as e:
    print(f"Connection error: {e}")

except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Logic

```python
import time
from pythaiid import ThaiIDCardReader, NoCardDetectedError

def read_with_retry(max_attempts=3, delay=1):
    reader = ThaiIDCardReader()

    for attempt in range(max_attempts):
        try:
            with reader.card_session():
                return reader.read_card()
        except NoCardDetectedError:
            if attempt < max_attempts - 1:
                print(f"No card detected. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise

# Usage
try:
    card = read_with_retry(max_attempts=5, delay=2)
    print(f"Success: {card.cid}")
except Exception as e:
    print(f"Failed after retries: {e}")
```

## Best Practices

### Resource Management

Always use context managers or ensure proper disconnection:

```python
# Good: Using context manager
with reader.card_session():
    card = reader.read_card()

# Also good: Manual control with try/finally
reader = ThaiIDCardReader()
try:
    reader.connect()
    card = reader.read_card()
finally:
    reader.disconnect()
```

### Performance Tips

1. **Skip photo if not needed** - Photo reading is the slowest operation
2. **Reuse reader instance** - Don't create new reader for each read
3. **Use specific reader index** - Faster than auto-detection
4. **Batch operations** - Read multiple cards without disconnecting reader

### Security Considerations

1. **Sanitize CID data** - Validate before storing in database
2. **Secure photo storage** - Photos contain sensitive biometric data
3. **Log access** - Maintain audit trail of card reads
4. **Encrypt at rest** - Store card data securely
5. **Comply with regulations** - Follow local data protection laws

## Next Steps

- [API Reference →](api-reference.md)
- [Troubleshooting →](troubleshooting.md)
