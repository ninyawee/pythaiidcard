# API Reference

## Core Classes

### ThaiIDCardReader

::: pythaiidcard.reader.ThaiIDCardReader
    options:
      show_source: true
      members:
        - __init__
        - list_readers
        - connect
        - disconnect
        - read_card
        - card_session

---

### ThaiIDCard

::: pythaiidcard.models.ThaiIDCard
    options:
      show_source: true
      members:
        - cid
        - thai_fullname
        - english_fullname
        - date_of_birth
        - gender
        - gender_text
        - card_issuer
        - issue_date
        - expire_date
        - address
        - photo
        - age
        - is_expired
        - days_until_expiry
        - save_photo
        - model_dump
        - model_dump_json

---

### CardReaderInfo

::: pythaiidcard.models.CardReaderInfo
    options:
      show_source: true

---

## Convenience Functions

### read_thai_id_card

::: pythaiidcard.reader.read_thai_id_card
    options:
      show_source: true

---

## Utility Functions

### CID Utilities

::: pythaiidcard.utils.validate_cid
    options:
      show_source: true

::: pythaiidcard.utils.format_cid
    options:
      show_source: true

---

### Date Utilities

::: pythaiidcard.utils.parse_buddhist_date
    options:
      show_source: true

::: pythaiidcard.utils.calculate_age
    options:
      show_source: true

::: pythaiidcard.utils.is_card_expired
    options:
      show_source: true

---

### Text Utilities

::: pythaiidcard.utils.thai_to_unicode
    options:
      show_source: true

::: pythaiidcard.utils.format_address
    options:
      show_source: true

---

## Exceptions

### ThaiIDCardException

::: pythaiidcard.exceptions.ThaiIDCardException
    options:
      show_source: true

---

### SystemDependencyError

::: pythaiidcard.exceptions.SystemDependencyError
    options:
      show_source: true

---

### NoReaderFoundError

::: pythaiidcard.exceptions.NoReaderFoundError
    options:
      show_source: true

---

### NoCardDetectedError

::: pythaiidcard.exceptions.NoCardDetectedError
    options:
      show_source: true

---

### CardConnectionError

::: pythaiidcard.exceptions.CardConnectionError
    options:
      show_source: true

---

### InvalidCardError

::: pythaiidcard.exceptions.InvalidCardError
    options:
      show_source: true

---

### CommandError

::: pythaiidcard.exceptions.CommandError
    options:
      show_source: true

---

### DataReadError

::: pythaiidcard.exceptions.DataReadError
    options:
      show_source: true

---

### InvalidReaderIndexError

::: pythaiidcard.exceptions.InvalidReaderIndexError
    options:
      show_source: true

---

### CardTimeoutError

::: pythaiidcard.exceptions.CardTimeoutError
    options:
      show_source: true

---

## System Check

### check_system_dependencies

::: pythaiidcard.system_check.check_system_dependencies
    options:
      show_source: true

---

### check_and_raise_if_missing

::: pythaiidcard.system_check.check_and_raise_if_missing
    options:
      show_source: true

---

## Constants

### APDUCommand

::: pythaiidcard.constants.APDUCommand
    options:
      show_source: true

---

### CardCommands

::: pythaiidcard.constants.CardCommands
    options:
      show_source: true

---

### ResponseStatus

::: pythaiidcard.constants.ResponseStatus
    options:
      show_source: true
