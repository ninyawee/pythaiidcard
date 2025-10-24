# Structured Data Models Update

## Overview

The `pythaiidcard` library has been enhanced with structured data models for Names and Addresses, similar to the Go package implementation. This provides better type safety, easier data access, and maintains full backward compatibility.

## What Changed

### New Models

#### 1. **Name Model** (`pythaiidcard/models.py`)

Parses raw name strings from Thai ID cards into structured components:

```python
from pythaiidcard.models import Name

# Parse from raw card data
name = Name.from_raw("นาย#สมชาย#วิชัย#ใจดี")

print(name.prefix)       # "นาย"
print(name.first_name)   # "สมชาย"
print(name.middle_name)  # "วิชัย"
print(name.last_name)    # "ใจดี"
print(name.full_name)    # "นายสมชาย วิชัย ใจดี" (computed)
```

#### 2. **Address Model** (`pythaiidcard/models.py`)

Parses raw address strings into structured components:

```python
from pythaiidcard.models import Address

# Parse from raw card data
address = Address.from_raw("123/45#หมู่ที่6#ถนนพระราม 4#ตำบลคลองเตย#อำเภอคลองเตย#จังหวัดกรุงเทพมหานคร")

print(address.house_no)     # "123/45"
print(address.moo)          # "6"
print(address.street)       # "ถนนพระราม 4"
print(address.subdistrict)  # "คลองเตย"
print(address.district)     # "คลองเตย"
print(address.province)     # "กรุงเทพมหานคร"
print(address.address)      # Full address with Thai prefixes (computed)
```

#### 3. **Updated ThaiIDCard Model**

The main model now uses structured sub-models:

**New Fields:**
- `thai_name: Name` (was `thai_fullname: str`)
- `english_name: Name` (was `english_fullname: str`)
- `address_info: Address` (was `address: str`)

**Backward Compatible Properties:**
- `thai_fullname` → Returns `thai_name.full_name`
- `english_fullname` → Returns `english_name.full_name`
- `address` → Returns `address_info.address`

## Usage Examples

### Structured Data Access (New)

```python
from pythaiidcard import ThaiIDCardReader

reader = ThaiIDCardReader()
with reader.card_session():
    card = reader.read_card()

    # Access structured name components
    print(f"First Name: {card.thai_name.first_name}")
    print(f"Last Name: {card.thai_name.last_name}")
    print(f"Prefix: {card.english_name.prefix}")

    # Access structured address components
    print(f"Province: {card.address_info.province}")
    print(f"District: {card.address_info.district}")
    print(f"House No: {card.address_info.house_no}")
    print(f"Soi: {card.address_info.soi}")
```

### Backward Compatible Access (Still Works)

```python
# Old code continues to work unchanged
print(f"Name: {card.thai_fullname}")
print(f"English: {card.english_fullname}")
print(f"Address: {card.address}")
```

## Benefits

### 1. **Type Safety**
```python
# Get typed access to components
province: str = card.address_info.province
first_name: str = card.thai_name.first_name
```

### 2. **Easier Data Extraction**
```python
# No need to parse strings manually
province = card.address_info.province  # Direct access
# vs
# province = card.address.split("จังหวัด")[-1]  # String parsing
```

### 3. **Better Validation**
- Name and Address parsing validates data format
- Automatic handling of Thai prefixes (หมู่ที่, ซอย, ตำบล, อำเภอ, จังหวัด)
- Handles Bangkok-specific prefixes (แขวง, เขต)

### 4. **JSON Export**
```python
# Structured data exports cleanly
card_json = card.model_dump_json(indent=2)
# Output includes nested name and address objects
```

### 5. **100% Backward Compatible**
- All existing code continues to work
- No breaking changes
- Migration is optional

## Address Parsing Features

The Address model intelligently handles:

- **Multiple formats**: Supports both "#" delimited and non-delimited addresses
- **Thai prefixes**: Automatically strips/adds prefixes as needed
  - หมู่ที่ (Moo/Village number)
  - ซอย (Soi/Lane)
  - ถนน (Street/Road)
  - ตำบล/แขวง (Subdistrict - rural/Bangkok)
  - อำเภอ/เขต (District - rural/Bangkok)
  - จังหวัด (Province)
- **Fallback parsing**: Handles incomplete or malformed addresses gracefully
- **Clean data storage**: Stores components without Thai prefixes, adds them in `address` property

## Migration Guide

No migration required! However, you can optionally update your code to use structured access:

### Before (Still Works)
```python
card = reader.read_card()
name = card.thai_fullname
province = card.address.split("จังหวัด")[-1] if "จังหวัด" in card.address else ""
```

### After (Recommended)
```python
card = reader.read_card()
name = card.thai_name.full_name
province = card.address_info.province
```

## Testing

A comprehensive test suite is included:

```bash
uv run python test_enhanced_models.py
```

Tests cover:
- Name parsing (Thai and English)
- Address parsing (various formats)
- ThaiIDCard integration
- Backward compatibility
- Data validation

## Technical Details

### Implementation
- **Pydantic validators**: Automatically parse raw strings into structured models
- **Computed properties**: `full_name` and `address` are dynamically generated
- **Type annotations**: Full type hints throughout
- **Immutable**: Models use Pydantic's immutability features

### Performance
- No performance impact
- Parsing happens once during model instantiation
- Computed properties are efficient

### Compatibility
- Python 3.13+
- Pydantic 2.0+
- All existing code continues to work unchanged

## Files Changed

- `pythaiidcard/models.py` - Added Name and Address models, updated ThaiIDCard
- `pythaiidcard/reader.py` - Updated to pass data to new field names
- `README.md` - Updated documentation
- `test_enhanced_models.py` - New test file

## Additional Features

### NHSO Health Insurance Data

The library also supports reading National Health Security Office (NHSO) health insurance data:

```python
reader = ThaiIDCardReader()
with reader.card_session():
    # Read main card data
    card = reader.read_card()

    # Read NHSO health insurance data
    nhso = reader.read_nhso_data()

    print(f"Main Hospital: {nhso.main_hospital_name}")
    print(f"Insurance: {nhso.main_inscl}")
    print(f"Expires: {nhso.expire_date}")
    print(f"Valid: {not nhso.is_expired}")
```

**NHSOData Model Fields:**
- `main_inscl`, `sub_inscl`: Insurance classification codes
- `main_hospital_name`, `sub_hospital_name`: Registered hospitals
- `paid_type`: Payment type code
- `issue_date`, `expire_date`, `update_date`: Date information
- `change_hospital_amount`: Number of hospital changes allowed
- `is_expired`, `days_until_expiry`: Computed properties

### Laser ID Support

Read the laser-engraved ID from the card:

```python
reader = ThaiIDCardReader()
with reader.card_session():
    laser_id = reader.read_laser_id()
    print(f"Laser ID: {laser_id}")
```

This reads the unique laser-engraved identifier on the physical card.

## Future Enhancements

Potential future improvements:
- Address validation against Thai postal database
- Name title normalization (นาย/Mr./etc.)
- Multi-language address formatting
- GeoJSON export for address coordinates
- NHSO hospital lookup/validation
