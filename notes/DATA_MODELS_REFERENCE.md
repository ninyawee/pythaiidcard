# Thai ID Card Data Models Reference

**File:** `pythaiidcard/models.py`

This document provides a comprehensive reference for all data models used in the Thai ID Card reader library, with special focus on **NHSO (National Health Security Office)** data and **Laser ID**.

---

## Table of Contents

1. [Main ID Card Data (`ThaiIDCard`)](#main-id-card-data-thaiidcard)
2. [NHSO Health Insurance Data (`NHSOData`)](#nhso-health-insurance-data-nhsodata)
3. [Laser ID (String)](#laser-id-string)
4. [Supporting Models](#supporting-models)
   - [Name Model](#name-model)
   - [Address Model](#address-model)
   - [CardReaderInfo Model](#cardreaderinfo-model)
5. [Usage Examples](#usage-examples)

---

## Main ID Card Data (`ThaiIDCard`)

**Location:** `models.py:254-406`

The primary model representing all personal information from a Thai National ID Card.

### Fields

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `cid` | `str` | ✅ Yes | 13-digit citizen identification number (validated with checksum) |
| `thai_name` | `Name` | ✅ Yes | Name in Thai language (object) |
| `english_name` | `Name` | ✅ Yes | Name in English (object) |
| `date_of_birth` | `date` | ✅ Yes | Date of birth (converted from Buddhist Era) |
| `gender` | `str` | ✅ Yes | Gender code: "1" = Male, "2" = Female |
| `card_issuer` | `str` | ✅ Yes | Card issuing organization (e.g., "กรมการปกครอง") |
| `issue_date` | `date` | ✅ Yes | Date when the card was issued |
| `expire_date` | `date` | ✅ Yes | Date when the card expires |
| `address_info` | `Address` | ✅ Yes | Registered address information (object) |
| `photo` | `bytes` | ❌ No | JPEG photo data (optional, 5,100 bytes) |

### Computed Fields

These fields are automatically calculated from other fields:

| Computed Field | Type | Description |
|----------------|------|-------------|
| `thai_fullname` | `str` | Full Thai name as string (e.g., "นายสมชาย ใจดี") |
| `english_fullname` | `str` | Full English name as string (e.g., "Mr.Somchai Jaidee") |
| `address` | `str` | Full address as formatted string |
| `age` | `int` | Current age calculated from date of birth |
| `gender_text` | `str` | Gender as text: "Male" or "Female" |
| `is_expired` | `bool` | Whether the card has expired |
| `days_until_expiry` | `int` | Days until card expiry (negative if expired) |

### Special Features

#### CID Validation

The `cid` field is validated using the Thai ID card checksum algorithm:

```python
# Example: Validating CID
# Valid CID: 1234567890121
# Last digit (1) is checksum calculated from first 12 digits

checksum = 0
for i in range(12):
    checksum += int(cid[i]) * (13 - i)
checksum = (11 - (checksum % 11)) % 10
# Must equal the 13th digit
```

#### Date Conversion

All dates are stored in **Buddhist Era (BE)** on the card and automatically converted to **Gregorian calendar**:

```python
# Card stores: 25380220 (Buddhist Era)
# Converts to: 1995-02-20 (Gregorian)
# Calculation: 2538 - 543 = 1995
```

### Example Data Structure

```python
ThaiIDCard(
    cid="1234567890121",
    thai_name=Name(prefix="นาย", first_name="สมชาย", middle_name="", last_name="ใจดี"),
    english_name=Name(prefix="Mr.", first_name="Somchai", middle_name="", last_name="Jaidee"),
    date_of_birth=date(1995, 2, 20),
    gender="1",
    card_issuer="กรมการปกครอง",
    issue_date=date(2017, 1, 1),
    expire_date=date(2027, 1, 1),
    address_info=Address(...),
    photo=b'\xff\xd8\xff\xe0...',  # JPEG bytes
)
```

---

## NHSO Health Insurance Data (`NHSOData`)

**Location:** `models.py:408-458`

**Reading Method:** `reader.read_nhso_data()`

Model representing **National Health Security Office** (สำนักงานหลักประกันสุขภาพแห่งชาติ) health insurance data stored on Thai ID cards.

### What is NHSO?

NHSO manages Thailand's Universal Health Coverage (UC) scheme (also called "30 Baht Scheme" or "Gold Card"). This data includes:
- Current health insurance status
- Registered hospital information
- Insurance classification
- Coverage dates

### Fields

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `main_inscl` | `str` | ✅ Yes | Main insurance classification code |
| `sub_inscl` | `str` | ✅ Yes | Sub insurance classification code |
| `main_hospital_name` | `str` | ✅ Yes | Main registered hospital name (Thai) |
| `sub_hospital_name` | `str` | ✅ Yes | Sub registered hospital name (Thai) |
| `paid_type` | `str` | ✅ Yes | Payment type code |
| `issue_date` | `date` | ✅ Yes | NHSO registration issue date |
| `expire_date` | `date` | ✅ Yes | NHSO registration expiry date |
| `update_date` | `date` | ✅ Yes | Last update date of NHSO record |
| `change_hospital_amount` | `str` | ✅ Yes | Number of times hospital was changed |

### Computed Fields

| Computed Field | Type | Description |
|----------------|------|-------------|
| `is_expired` | `bool` | Whether the NHSO registration has expired |
| `days_until_expiry` | `int` | Days until NHSO registration expiry |

### Insurance Classification Codes

The `main_inscl` and `sub_inscl` codes indicate the type of health coverage:

**Common Main Classifications:**
- `UCS` - Universal Coverage Scheme (30 Baht)
- `SSS` - Social Security Scheme
- `CSMBS` - Civil Servant Medical Benefit Scheme
- `LGO` - Local Government Organization
- `OFC` - Other Free Coverage

**Sub Classifications:**
- Typically indicate special programs or conditions within the main classification

### Example NHSO Data

```python
NHSOData(
    main_inscl="UCS",
    sub_inscl="",
    main_hospital_name="โรงพยาบาลบางกะปิ",
    sub_hospital_name="",
    paid_type="01",
    issue_date=date(2020, 1, 1),
    expire_date=date(2025, 12, 31),
    update_date=date(2024, 6, 15),
    change_hospital_amount="2",
)
```

### Reading NHSO Data

```python
from pythaiidcard import ThaiIDCardReader

reader = ThaiIDCardReader(reader_index=0)
reader.connect()

# Read NHSO data (requires separate applet selection)
nhso_data = reader.read_nhso_data()

print(f"Hospital: {nhso_data.main_hospital_name}")
print(f"Classification: {nhso_data.main_inscl}")
print(f"Expires: {nhso_data.expire_date}")
print(f"Is Expired: {nhso_data.is_expired}")

reader.disconnect()
```

### NHSO APDU Commands

**Location:** `constants.py` (lines related to NHSO)

The NHSO data is read from a separate applet on the card:

1. **Select NHSO Applet:** `A0 00 00 00 54 48 00 07`
2. **Read Fields:** Individual APDU commands for each field
   - `NHSO_MAIN_INSCL`
   - `NHSO_SUB_INSCL`
   - `NHSO_MAIN_HOSPITAL_NAME`
   - `NHSO_SUB_HOSPITAL_NAME`
   - `NHSO_PAID_TYPE`
   - `NHSO_ISSUE_DATE`
   - `NHSO_EXPIRE_DATE`
   - `NHSO_UPDATE_DATE`
   - `NHSO_CHANGE_HOSPITAL_AMOUNT`

### Important Notes

⚠️ **NHSO data requires separate read operation:**
- Not included in `read_card()` by default
- Must call `read_nhso_data()` explicitly
- Requires selecting NHSO applet (separate from personal data applet)

⚠️ **NHSO data may not exist on all cards:**
- Some cards may not have NHSO applet
- Reading may fail if card doesn't support NHSO data
- Handle exceptions appropriately

---

## Laser ID (String)

**Location:** `reader.py:409-433`

**Reading Method:** `reader.read_laser_id()`

**Data Type:** `str` (not a model object)

### What is Laser ID?

The **Laser ID** is a **laser-engraved identification number** physically etched onto Thai ID cards. It's a security feature separate from the electronic CID stored in the chip.

### Characteristics

- **Format:** 7-byte string (typically alphanumeric)
- **Location:** Laser-engraved on the physical card surface
- **Purpose:** Additional security/verification feature
- **Storage:** Stored electronically on the Card applet

### Reading Laser ID

```python
from pythaiidcard import ThaiIDCardReader

reader = ThaiIDCardReader(reader_index=0)
reader.connect()

# Read laser ID (requires separate applet selection)
laser_id = reader.read_laser_id()

print(f"Laser ID: {laser_id}")
# Example output: "AB12345"

reader.disconnect()
```

### Laser ID APDU Command

**Location:** `constants.py:149-151`

```python
LASER_ID = APDUCommand(
    cmd=bytes.fromhex("80 B0 00 16 02 00 07"),
    description="Laser engraved ID (7 bytes)"
)
```

The laser ID is read from the **Card applet** (not the personal data applet):

1. **Select Card Applet:** `A0 00 00 00 54 48 00 03`
2. **Read Laser ID:** `80 B0 00 16 02 00 07`

### Important Notes

⚠️ **Laser ID requires separate read operation:**
- Not included in `read_card()` by default
- Must call `read_laser_id()` explicitly
- Requires selecting Card applet (separate from personal data applet)

⚠️ **No dedicated model:**
- Unlike NHSO data, Laser ID is just a string
- No validation or computed fields
- Simple text value

---

## Supporting Models

### Name Model

**Location:** `models.py:10-46`

Represents a person's name (Thai or English).

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prefix` | `str` | ✅ Yes | Name prefix (e.g., "นาย", "นาง", "Mr.", "Mrs.") |
| `first_name` | `str` | ✅ Yes | First name |
| `middle_name` | `str` | ❌ No | Middle name (may be empty) |
| `last_name` | `str` | ✅ Yes | Last name |

#### Computed Fields

| Field | Type | Description |
|-------|------|-------------|
| `full_name` | `str` | Complete formatted name (prefix + first + middle + last) |

#### Raw Format

Names on the card are stored with `#` delimiters:

```
นาย#สมชาย#วิชัย#ใจดี
-> prefix="นาย", first_name="สมชาย", middle_name="วิชัย", last_name="ใจดี"
-> full_name="นายสมชาย วิชัย ใจดี"
```

---

### Address Model

**Location:** `models.py:49-251`

Represents a Thai postal address.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `house_no` | `str` | ✅ Yes | House number (บ้านเลขที่) |
| `moo` | `str` | ❌ No | Village/Moo number (หมู่ที่) |
| `soi` | `str` | ❌ No | Soi/Lane (ซอย) |
| `street` | `str` | ❌ No | Street/Road (ถนน) |
| `subdistrict` | `str` | ✅ Yes | Subdistrict/Tambon (ตำบล/แขวง) |
| `district` | `str` | ✅ Yes | District/Amphoe (อำเภอ/เขต) |
| `province` | `str` | ✅ Yes | Province (จังหวัด) |

#### Computed Fields

| Field | Type | Description |
|-------|------|-------------|
| `address` | `str` | Fully formatted address string with Thai prefixes |

#### Example

```python
Address(
    house_no="123/45",
    moo="5",
    soi="ลาดพร้าว 15",
    street="ถนนลาดพร้าว",
    subdistrict="บางกะปิ",
    district="บางกะปิ",
    province="กรุงเทพมหานคร"
)
# address = "123/45 หมู่ที่5 ซอยลาดพร้าว 15 ถนนลาดพร้าว ตำบลบางกะปิ อำเภอบางกะปิ จังหวัดกรุงเทพมหานคร"
```

---

### CardReaderInfo Model

**Location:** `models.py:461-467`

Information about a connected smart card reader.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `index` | `int` | ✅ Yes | Reader index in the system (0, 1, 2, ...) |
| `name` | `str` | ✅ Yes | Reader name/model (e.g., "Alcor Link AK9563 00 00") |
| `atr` | `str` | ❌ No | Answer to Reset (ATR) hex string |
| `connected` | `bool` | ❌ No | Whether a card is connected (default: False) |

#### Example

```python
CardReaderInfo(
    index=0,
    name="Alcor Link AK9563 00 00",
    atr="3B 79 96 00 00 54 48 20 4E 49 44 20 31 37",
    connected=True
)
```

---

## Usage Examples

### Reading All Data Types

```python
from pythaiidcard import ThaiIDCardReader

reader = ThaiIDCardReader(reader_index=0)

with reader.card_session():
    # 1. Read main ID card data (with photo)
    card_data = reader.read_card(include_photo=True)

    print("=== PERSONAL DATA ===")
    print(f"CID: {card_data.cid}")
    print(f"Thai Name: {card_data.thai_fullname}")
    print(f"English Name: {card_data.english_fullname}")
    print(f"Date of Birth: {card_data.date_of_birth}")
    print(f"Age: {card_data.age}")
    print(f"Gender: {card_data.gender_text}")
    print(f"Address: {card_data.address}")
    print(f"Issue Date: {card_data.issue_date}")
    print(f"Expire Date: {card_data.expire_date}")
    print(f"Is Expired: {card_data.is_expired}")

    if card_data.photo:
        card_data.save_photo("photo.jpg")
        print(f"Photo saved: photo.jpg")

    # 2. Read NHSO health insurance data
    try:
        nhso_data = reader.read_nhso_data()

        print("\n=== NHSO HEALTH INSURANCE ===")
        print(f"Classification: {nhso_data.main_inscl}")
        print(f"Main Hospital: {nhso_data.main_hospital_name}")
        print(f"Sub Hospital: {nhso_data.sub_hospital_name}")
        print(f"Issue Date: {nhso_data.issue_date}")
        print(f"Expire Date: {nhso_data.expire_date}")
        print(f"Is Expired: {nhso_data.is_expired}")
        print(f"Days Until Expiry: {nhso_data.days_until_expiry}")
        print(f"Hospital Changes: {nhso_data.change_hospital_amount}")

    except Exception as e:
        print(f"NHSO data not available: {e}")

    # 3. Read Laser ID
    try:
        laser_id = reader.read_laser_id()

        print("\n=== LASER ID ===")
        print(f"Laser ID: {laser_id}")

    except Exception as e:
        print(f"Laser ID not available: {e}")
```

### JSON Export Example

```python
import json
from datetime import date

# Custom JSON encoder for date objects
class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

# Read card
card_data = reader.read_card(include_photo=False)

# Convert to dict
card_dict = card_data.model_dump()

# Export to JSON
json_output = json.dumps(card_dict, cls=DateEncoder, ensure_ascii=False, indent=2)
print(json_output)

# Save to file
with open("card_data.json", "w", encoding="utf-8") as f:
    json.dump(card_dict, f, cls=DateEncoder, ensure_ascii=False, indent=2)
```

### API Response Example

```python
# For API server responses (from card_monitor.py)
card_dict = card_data.model_dump()

# Convert photo to base64 if present
if card_dict.get("photo"):
    import base64
    photo_bytes = card_dict["photo"]
    card_dict["photo_base64"] = f"data:image/jpeg;base64,{base64.b64encode(photo_bytes).decode('utf-8')}"
    del card_dict["photo"]  # Remove raw bytes

# Send via WebSocket or REST API
response = {
    "type": "card_read",
    "data": card_dict,
    "cached": False,
    "read_at": datetime.now().isoformat()
}
```

---

## Field Name Quick Reference

### API Response Field Names (for web app)

When accessing fields from `model_dump()`:

| Display Label | Field Name (API) | Type |
|---------------|------------------|------|
| Citizen ID | `cid` | `str` |
| Thai Name | `thai_fullname` | `str` (computed) |
| English Name | `english_fullname` | `str` (computed) |
| Date of Birth | `date_of_birth` | `str` (ISO format) |
| Gender | `gender_text` | `str` (computed) |
| Address | `address` | `str` (computed) |
| Issue Date | `issue_date` | `str` (ISO format) |
| Expire Date | `expire_date` | `str` (ISO format) |
| Photo | `photo_base64` | `str` (data URI) |
| Age | `age` | `int` (computed) |
| Is Expired | `is_expired` | `bool` (computed) |

### NHSO Field Names

| Display Label | Field Name | Type |
|---------------|------------|------|
| Insurance Type | `main_inscl` | `str` |
| Sub Type | `sub_inscl` | `str` |
| Main Hospital | `main_hospital_name` | `str` |
| Sub Hospital | `sub_hospital_name` | `str` |
| Payment Type | `paid_type` | `str` |
| Issue Date | `issue_date` | `str` (ISO format) |
| Expire Date | `expire_date` | `str` (ISO format) |
| Updated | `update_date` | `str` (ISO format) |
| Hospital Changes | `change_hospital_amount` | `str` |

---

## Data Reading Workflow

```
┌─────────────────────────────────────────────┐
│  Thai ID Card (Smart Card)                  │
├─────────────────────────────────────────────┤
│                                             │
│  Applet 1: Personal Data                   │
│  ├─ CID, Name, DOB, Gender                 │
│  ├─ Address, Issue/Expire dates            │
│  └─ Photo (20 parts, 5100 bytes)           │
│                                             │
│  Applet 2: NHSO Data                       │
│  ├─ Insurance classification               │
│  ├─ Hospital registration                  │
│  └─ Coverage dates                         │
│                                             │
│  Applet 3: Card Data                       │
│  └─ Laser ID (7 bytes)                     │
│                                             │
└─────────────────────────────────────────────┘
        │
        ↓ PC/SC APDU Commands
        │
┌─────────────────────────────────────────────┐
│  ThaiIDCardReader                           │
├─────────────────────────────────────────────┤
│  read_card()         → ThaiIDCard           │
│  read_nhso_data()    → NHSOData             │
│  read_laser_id()     → str                  │
└─────────────────────────────────────────────┘
        │
        ↓
┌─────────────────────────────────────────────┐
│  Pydantic Models                            │
├─────────────────────────────────────────────┤
│  ThaiIDCard.model_dump()                    │
│  NHSOData.model_dump()                      │
└─────────────────────────────────────────────┘
        │
        ↓
┌─────────────────────────────────────────────┐
│  API / Web App / Storage                    │
└─────────────────────────────────────────────┘
```

---

## Summary

| Data Type | Model Class | Reading Method | Applet Required | Included in `read_card()` |
|-----------|-------------|----------------|-----------------|--------------------------|
| **Personal Data** | `ThaiIDCard` | `read_card()` | Personal Data Applet | ✅ Yes |
| **Photo** | `bytes` (part of ThaiIDCard) | `read_card(include_photo=True)` | Personal Data Applet | ✅ Yes (optional) |
| **NHSO Data** | `NHSOData` | `read_nhso_data()` | NHSO Applet | ❌ No |
| **Laser ID** | `str` (not a model) | `read_laser_id()` | Card Applet | ❌ No |

---

**Version:** 2.3.0
**Date:** 2025-10-24
**File:** `pythaiidcard/models.py`
