# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`thai_idcard_reader_test` is a proof-of-concept Flutter application for testing Thai National ID card reading using the `ccid` package. This is part of research to create a Flutter version of the [pythaiidcard](https://github.com/ninyawee/pythaiidcard) Python library.

**Current Status:** Minimal Flutter boilerplate - CCID integration not yet implemented in UI layer.

## Development Commands

### Environment Setup
```bash
# Install dependencies
flutter pub get

# Clean and reinstall (if needed)
flutter clean && flutter pub get
```

### Running the Application
```bash
# Run on connected device (debug mode)
flutter run

# Run on specific device
flutter devices                    # List available devices
flutter run -d <device-id>        # Run on specific device

# Run in release mode
flutter run --release

# Build for specific platform
flutter build apk                  # Android APK
flutter build ios                  # iOS (requires macOS + Xcode)
```

### Code Quality
```bash
# Analyze code for issues
flutter analyze

# Format code
dart format lib test

# Run tests
flutter test

# Run specific test file
flutter test test/widget_test.dart
```

## Architecture

### Current Implementation

**Single-file app structure** in `lib/main.dart`:
- Flutter boilerplate counter demo (not production code)
- Simple Material Design app with `ColorScheme.fromSeed(Colors.deepPurple)`
- State management: Basic `setState()` in `StatefulWidget`
- No CCID integration yet - needs implementation

### Expected CCID Integration Flow

Thai ID cards use ISO 7816-4 APDU commands over PC/SC (same as Python implementation):

1. **Card Detection**: Use `ccid` package to enumerate readers and detect card insertion
2. **Card Selection**: Send `SELECT APPLET` command with Thai ID applet identifier `A0 00 00 00 54 48 00 01`
3. **Response Handling**: Accept both `90 00` (success) and `61 XX` (success with more data) as valid responses
4. **Data Reading**: Each field requires two commands:
   - Initial command (e.g., `80 B0 00 04 02 00 0D` for CID)
   - GET RESPONSE command (varies by ATR)
5. **Photo Reading**: Assemble 20 separate 255-byte chunks (5,100 bytes total JPEG)

### Thai ID Card Data Fields

All fields available from Python `pythaiidcard` library:
- CID (Citizen ID): 13 digits
- Thai Full Name
- English Full Name
- Date of Birth (Buddhist Era format `YYYYMMDD`, subtract 543 for Gregorian)
- Gender
- Address
- Issue Date / Expiry Date
- Photo (JPEG, 20 parts × 255 bytes)

### Date Handling

Thai ID cards store dates in Buddhist Era (BE):
- Buddhist Era year = Gregorian year + 543
- Example: `25380220` = February 20, 1995 (2538 - 543 = 1995)
- Must convert when parsing dates

## Dependencies

### Production Dependencies

```yaml
dependencies:
  flutter: sdk
  cupertino_icons: ^1.0.8    # iOS-style icons
  ccid: ^0.1.8               # CCID smartcard reading
```

**Important:** The `ccid` package version was corrected from `^0.3.0` (non-existent) to `^0.1.8` (available).

### CCID Package Details

- **Purpose:** Smart card reading using CCID protocol with PC/SC-like APIs
- **Platform Support:**
  - iOS ✅ (iOS 13.0+, requires MFi-certified smartcard reader + entitlements)
  - Android ✅ (requires USB OTG smartcard reader + permissions)
  - macOS ✅ (built-in CryptoTokenKit support)
  - Linux ❌ (not included in this test)
  - Windows ❌ (not supported by ccid package)
- **Key Dependencies:** `dart_pcsc`, `ffi`, `platform_detector`, `universal_io`

### Dev Dependencies

```yaml
dev_dependencies:
  flutter_test: sdk
  flutter_lints: ^5.0.0      # Dart linting rules
```

## Platform-Specific Configuration

### Android Setup

**Required:** Add USB permissions to `android/app/src/main/AndroidManifest.xml`:

```xml
<!-- Add before <application> tag -->
<uses-feature android:name="android.hardware.usb.host" />
<uses-permission android:name="android.permission.USB_PERMISSION" />
```

**Status:** ⚠️ Not yet added to manifest (line 46 in AndroidManifest.xml)

**Build Configuration:**
- Kotlin DSL (modern Gradle)
- Min SDK: Flutter default (typically API 21+)
- Compile SDK: Flutter default
- Target: `android/app/src/main/kotlin/com/example/thai_idcard_reader_test/MainActivity.kt`

### iOS Setup

**Required:** Create entitlements file `ios/Runner/Runner.entitlements`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/PropertyLists/DTD/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.smartcard</key>
    <true/>
</dict>
</plist>
```

**Status:** ⚠️ File does not exist yet

**Build Configuration:**
- iOS 13.0+ required (from ccid package)
- Swift-based AppDelegate in `ios/Runner/AppDelegate.swift`
- Standard Flutter plugin registration
- Requires MFi-certified smartcard readers (Lightning or USB-C)

## Hardware Requirements

**⚠️ Critical:** Thai National ID cards do NOT support NFC. External smartcard reader is mandatory.

### Recommended Readers

**For Android (USB OTG):**
- ACS ACR39U-NF PocketMate II (USB Type-C)
- ACS ACR122U (USB-A with OTG adapter)
- Requires USB OTG support on device

**For iOS (MFi-certified):**
- Identiv uTrust 3700 F
- Feitian iR301-U
- ACS CryptoMate series (MFi-certified models)
- Requires Lightning or USB-C connection

**For Testing:** Any PC/SC compatible reader (e.g., Alcor Link AK9563)

## Implementation Roadmap

Based on README.md, next steps are:

1. **Card Detection:**
   - Import `ccid` package in `main.dart`
   - List available readers
   - Detect card insertion

2. **APDU Commands:**
   - Port command definitions from `pythaiidcard/constants.py`
   - Implement SELECT APPLET (`A0 00 00 00 54 48 00 01`)
   - Handle response codes (`90 00` and `61 XX` both mean success)

3. **Data Reading:**
   - Port field reading logic from `pythaiidcard/reader.py`
   - Implement CID, name, DOB, address extraction
   - Handle Buddhist Era date conversion

4. **Photo Assembly:**
   - Read 20 × 255-byte JPEG chunks
   - Concatenate to form complete 5,100-byte photo
   - Progress callback support for UI

5. **UI Implementation:**
   - Replace counter demo with card reader interface
   - Display card data fields
   - Show extracted photo
   - Error handling UI

6. **Data Models:**
   - Create Dart models (consider `freezed` or `json_serializable`)
   - CID checksum validation (mod-11 algorithm from Python)
   - Gender parsing, age calculation, expiry checking

## Testing Strategy

### Current Tests

**File:** `test/widget_test.dart`
- Basic counter widget smoke test only
- No CCID or card reading tests

### Future Testing Needs

1. **Unit Tests:**
   - Date conversion (BE to Gregorian)
   - CID checksum validation
   - APDU command formatting
   - Photo assembly logic

2. **Integration Tests:**
   - Reader enumeration
   - Card connection
   - Data field reading
   - Error handling (no reader, no card, connection failures)

3. **Widget Tests:**
   - UI state changes
   - Error message display
   - Photo rendering

4. **Hardware Tests:**
   - Test with actual Thai ID cards
   - Verify against Python `pythaiidcard` output
   - Multiple reader types

## Related Documentation

- **Parent Project:** `pythaiidcard` (../../README.md)
- **Flutter Research:** `notes/FLUTTER_LIBRARY_RESEARCH.md` (../../notes/)
- **Python Implementation:** Reference for APDU commands and data parsing logic
- **CCID Package:** https://pub.dev/packages/ccid

## Critical Implementation Notes

### Response Status Handling

The SELECT APPLET command returns `61 0A` (success with 10 bytes more data), NOT `90 00`. Always accept BOTH:
- `90 00`: Standard success
- `61 XX`: Success with more data available (XX = number of bytes)

This is consistent with Python `pythaiidcard/constants.py` ResponseStatus.is_success() method.

### ATR-based Command Selection

Different card readers return different ATR (Answer To Reset) values. Adjust GET RESPONSE command accordingly:
- ATR starting with `3B 67`: Use `00 C0 00 01`
- All others: Use `00 C0 00 00`

See Python `pythaiidcard/constants.py` CardCommands.get_read_request() for reference.

### Buddhist Era Dates

All date fields use Buddhist Era format `YYYYMMDD`:
- Issue date, expiry date, date of birth
- Convert: Gregorian year = BE year - 543
- Example: `25380220` → 1995-02-20

## File Organization

```
thai_idcard_reader_test/
├── lib/
│   └── main.dart              # Main app (boilerplate, needs CCID implementation)
├── test/
│   └── widget_test.dart       # Basic tests (expand for CCID)
├── android/                   # Android platform code
│   └── app/src/main/AndroidManifest.xml  # ⚠️ Needs USB permissions
├── ios/                       # iOS platform code
│   └── Runner/                # ⚠️ Needs Runner.entitlements file
├── pubspec.yaml              # Dependencies (ccid: ^0.1.8)
├── README.md                 # Project documentation
└── CLAUDE.md                 # This file
```

## Debugging Tips

When implementing CCID integration:

1. **Reader Issues:**
   - Run on physical device (not emulator/simulator)
   - Ensure reader is connected before app launch
   - Check device supports USB OTG (Android) or MFi reader (iOS)

2. **Permission Issues:**
   - Verify USB permissions in AndroidManifest.xml
   - Verify smartcard entitlement in iOS entitlements
   - Check runtime permission prompts (Android)

3. **Card Reading Issues:**
   - Verify ATR matches Thai ID card format (`3B 79 96 00 00 54 48 20 4E 49 44 20 31 37`)
   - Check SELECT APPLET returns `61 0A` or `90 00`
   - Validate response handling accepts `61 XX` as success
   - Compare output with Python `pythaiidcard` library

4. **Development:**
   - Use `flutter run` with hot reload for rapid iteration
   - Add debug logging for APDU commands and responses
   - Test with actual Thai ID cards, not simulations

## Comparison with Python Implementation

This Flutter project mirrors the Python `pythaiidcard` library:

| Python | Flutter (Expected) |
|--------|-------------------|
| `pyscard` | `ccid` package |
| `pythaiidcard/reader.py` | Main app CCID logic |
| `pythaiidcard/constants.py` | APDU command definitions |
| `pythaiidcard/models.py` | Dart data models (freezed/json_serializable) |
| `pythaiidcard/utils.py` | Date/CID validation functions |
| `debug/app_compact.py` (Streamlit) | Flutter Material UI |

Use Python implementation as reference for APDU commands, response parsing, and data validation logic.
