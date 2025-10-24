#!/usr/bin/env python3
"""Test script for enhanced Name and Address models."""

from pythaiidcard.models import Name, Address, ThaiIDCard
from datetime import date


def test_name_parsing():
    """Test Name model parsing."""
    print("Testing Name model...")

    # Test Thai name
    thai_raw = "นาย#สมชาย#วิชัย#ใจดี"
    thai_name = Name.from_raw(thai_raw)
    assert thai_name.prefix == "นาย"
    assert thai_name.first_name == "สมชาย"
    assert thai_name.middle_name == "วิชัย"
    assert thai_name.last_name == "ใจดี"
    assert thai_name.full_name == "นายสมชาย วิชัย ใจดี"
    print(f"  Thai name: {thai_name.full_name} ✓")

    # Test English name
    eng_raw = "Mr.#Somchai#Vichai#Jaidee"
    eng_name = Name.from_raw(eng_raw)
    assert eng_name.prefix == "Mr."
    assert eng_name.first_name == "Somchai"
    assert eng_name.middle_name == "Vichai"
    assert eng_name.last_name == "Jaidee"
    assert eng_name.full_name == "Mr.Somchai Vichai Jaidee"
    print(f"  English name: {eng_name.full_name} ✓")

    # Test name without middle name
    simple_raw = "นาง#สมหญิง##ใจงาม"
    simple_name = Name.from_raw(simple_raw)
    assert simple_name.middle_name == ""
    assert simple_name.full_name == "นางสมหญิง ใจงาม"
    print(f"  Simple name: {simple_name.full_name} ✓")

    print("✓ Name model tests passed!\n")


def test_address_parsing():
    """Test Address model parsing."""
    print("Testing Address model...")

    # Test full address with # delimiters
    addr_raw = "123/45#หมู่ที่6#ถนนพระราม 4#ตำบลคลองเตย#อำเภอคลองเตย#จังหวัดกรุงเทพมหานคร"
    address = Address.from_raw(addr_raw)
    assert address.house_no == "123/45"
    assert address.moo == "6"
    assert address.street == "ถนนพระราม 4"
    assert address.subdistrict == "คลองเตย"
    assert address.district == "คลองเตย"
    assert address.province == "กรุงเทพมหานคร"
    print(f"  Full address: {address.address} ✓")

    # Test address with Soi instead of Moo
    addr_raw2 = "88#ซอยสุขุมวิท 11##ตำบลคลองเตยเหนือ#เขตวัฒนา#จังหวัดกรุงเทพมหานคร"
    address2 = Address.from_raw(addr_raw2)
    assert address2.soi == "สุขุมวิท 11"
    assert address2.moo == ""
    print(f"  Soi address: {address2.address} ✓")

    print("✓ Address model tests passed!\n")


def test_thai_id_card():
    """Test ThaiIDCard model with structured data."""
    print("Testing ThaiIDCard model...")

    # Test creating ThaiIDCard with raw strings (will be parsed)
    card_data = {
        "cid": "1234567890123",  # Note: This is a fake CID, won't pass checksum
        "thai_name": "นาย#สมชาย#วิชัย#ใจดี",
        "english_name": "Mr.#Somchai#Vichai#Jaidee",
        "date_of_birth": "25380220",  # Buddhist Era: Feb 20, 2538 = 1995
        "gender": "1",
        "card_issuer": "สำนักงานเขตบางรัก",
        "issue_date": "25600101",
        "expire_date": "25700101",
        "address_info": "123/45#หมู่ที่6#ถนนพระราม 4#ตำบลคลองเตย#อำเภอคลองเตย#จังหวัดกรุงเทพมหานคร",
    }

    try:
        # This will fail CID validation, but we can test without it
        card = ThaiIDCard(**card_data)
    except ValueError as e:
        print(f"  Expected CID validation error: {e}")
        # Use a valid CID instead (this one has correct checksum)
        # Calculate checksum for 110080044789X where X is the checksum digit
        # Checksum formula: (11 - (sum of (digit[i] * (13-i)) for i in 0..11) % 11) % 10
        cid_base = "110080044789"
        checksum = 0
        for i in range(12):
            checksum += int(cid_base[i]) * (13 - i)
        checksum = (11 - (checksum % 11)) % 10
        card_data["cid"] = cid_base + str(checksum)
        print(f"  Using valid CID: {card_data['cid']}")

        card = ThaiIDCard(**card_data)

        # Test that names were parsed correctly
        assert isinstance(card.thai_name, Name)
        assert card.thai_name.first_name == "สมชาย"
        print(f"  Thai name parsed: {card.thai_fullname} ✓")

        assert isinstance(card.english_name, Name)
        assert card.english_name.first_name == "Somchai"
        print(f"  English name parsed: {card.english_fullname} ✓")

        # Test that address was parsed correctly
        assert isinstance(card.address_info, Address)
        assert card.address_info.house_no == "123/45"
        assert card.address_info.province == "กรุงเทพมหานคร"
        print(f"  Address parsed: {card.address} ✓")

        # Test backward compatibility properties
        assert card.thai_fullname == "นายสมชาย วิชัย ใจดี"
        assert card.english_fullname == "Mr.Somchai Vichai Jaidee"
        assert len(card.address) > 0
        print("  Backward compatibility properties work ✓")

        # Test other computed fields
        print(f"  Age: {card.age} years old ✓")
        print(f"  Gender: {card.gender_text} ✓")
        print(f"  Expired: {card.is_expired} ✓")

    print("✓ ThaiIDCard model tests passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Enhanced Thai ID Card Models")
    print("=" * 60 + "\n")

    test_name_parsing()
    test_address_parsing()
    test_thai_id_card()

    print("=" * 60)
    print("✓ All tests passed successfully!")
    print("=" * 60)
