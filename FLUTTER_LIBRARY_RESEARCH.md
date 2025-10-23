# Flutter Library Research: Thai ID Card Reader

**Date:** October 23, 2025
**Purpose:** Research on converting the `pythaiidcard` Python library to Flutter

## Executive Summary

Based on comprehensive research, there are **existing Flutter solutions** for Thai ID card reading, and multiple technical approaches available for creating a Flutter implementation. The recommended approach depends on your target platforms and hardware requirements.

---

## Existing Flutter Solutions

### 1. **thai_idcard_reader_flutter** (Most Relevant)
- **Package:** `thai_idcard_reader_flutter` v0.0.7
- **Purpose:** Direct plugin for reading Thai ID cards with ACS smartcard readers
- **Platform Support:**
  - Android 5.0+ ✅
  - iOS ❌ (Not available)
- **Hardware:** ACS ACR39U-NF PocketMate II Smart Card Reader (USB Type-C)
- **Status:** Published on pub.dev
- **Note:** Specifically designed for Thai ID cards with ACS readers

### 2. **flutter_pcsc** (Generic PC/SC Solution)
- **Repository:** https://github.com/fabienrousseau/flutter_pcsc
- **Purpose:** Generic PC/SC smartcard reader support
- **Platform Support:**
  - Linux ✅ (requires pcscd, libpcsclite1)
  - macOS ✅
  - Windows ✅
  - iOS ❌
  - Android ❌
- **License:** MIT
- **Use Case:** Desktop applications (Windows/macOS/Linux)
- **API:** Provides low-level APDU command interface

### 3. **ccid**
- **Package:** `ccid`
- **Purpose:** Smart card reading using CCID protocol with PC/SC-like APIs
- **Platform Support:**
  - Linux ✅ (requires dart_pcsc, PCSCLite)
  - macOS ✅ (requires CryptoTokenKit, com.apple.security.smartcard entitlement)
  - iOS ✅ (iOS 13.0+, requires com.apple.security.smartcard entitlement)
  - Android ❌
- **Use Case:** iOS/macOS apps with smartcard support

### 4. **flutter_nfc_kit** (NFC Alternative)
- **Package:** `flutter_nfc_kit`
- **Purpose:** NFC reading with ISO 7816 APDU support
- **Platform Support:**
  - Android ✅
  - iOS ✅ (requires AID specification in Info.plist)
- **Use Case:** Mobile NFC-enabled Thai ID card reading
- **Note:** Thai ID cards support NFC in newer versions

### 5. **acs-nfc-reader**
- **Repository:** https://github.com/ijazfx/acs-nfc-reader
- **Purpose:** Flutter plugin for PC/SC, ISO 14443 USB Reader
- **Hardware:** ACS readers
- **Use Case:** ACS hardware integration

---

## Related Implementations (Other Platforms)

### Node.js Implementation
- **Repository:** https://github.com/privageapp/thai-national-id-reader
- **Platform:** Node.js using PCSClite
- **Value:** Reference implementation for Thai ID card APDU commands

### Android Native Library
- **Repository:** https://github.com/Advanced-Logic/AndroidThaiNationalIDCard
- **Platform:** Native Android
- **Value:** Android-specific Thai ID card implementation

### Python Reference (Current Project)
- **Repository:** pythaiidcard (this project)
- **Platform:** Python with pyscard
- **Value:** Well-documented APDU command flow and data parsing

---

## Technical Approaches for Flutter Implementation

### Approach 1: Use Existing `thai_idcard_reader_flutter` (Quickest)
**Recommended for:** Android-only mobile apps with ACS readers

**Pros:**
- Ready-to-use solution
- Tested with Thai ID cards
- Minimal development effort

**Cons:**
- Android only (no iOS)
- Limited to ACS ACR39U hardware
- May lack features from pythaiidcard (photo reading, etc.)
- Unknown maintenance status (v0.0.7)

**Implementation:**
```yaml
# pubspec.yaml
dependencies:
  thai_idcard_reader_flutter: ^0.0.7
```

### Approach 2: Build on `flutter_pcsc` (Desktop Focus)
**Recommended for:** Windows/macOS/Linux desktop applications

**Pros:**
- Works across all major desktop platforms
- Generic PC/SC support (any reader)
- Active maintenance
- MIT license

**Cons:**
- No mobile platform support
- Requires implementing Thai ID card logic from scratch
- Need to port APDU commands from pythaiidcard

**Implementation Strategy:**
1. Use `flutter_pcsc` for low-level PC/SC communication
2. Port APDU commands from `pythaiidcard/constants.py`
3. Implement data parsing from `pythaiidcard/models.py`
4. Handle ATR detection and GET RESPONSE commands

**Example Pseudocode:**
```dart
import 'package:flutter_pcsc/flutter_pcsc.dart';

class ThaiIDCardReader {
  Future<ThaiIDCard> readCard() async {
    // Connect to card
    final context = await Pcsc.establishContext(Scope.user);
    final card = await context.connect(readerName, ShareMode.shared, Protocol.t1);

    // Send SELECT APPLET (A0 00 00 00 54 48 00 01)
    final selectResponse = await card.transmit(selectApduCommand);

    // Check for 61 0A or 90 00 response
    if (!isSuccess(selectResponse)) {
      throw Exception('Failed to select Thai ID applet');
    }

    // Read CID, name, etc. using APDU commands
    final cid = await readField(card, CID_COMMAND);
    final name = await readField(card, NAME_COMMAND);
    // ... more fields

    return ThaiIDCard(cid: cid, name: name, ...);
  }
}
```

### Approach 3: Hybrid with Platform Channels
**Recommended for:** Maximum platform coverage with existing native code

**Pros:**
- Can reuse pythaiidcard Python code on desktop
- Can use native Android/iOS libraries for mobile
- Full platform coverage
- Async communication model

**Cons:**
- Complex architecture (multiple native implementations)
- Requires maintaining platform-specific code
- Performance overhead from channel communication

**Implementation:**
```dart
// Dart side
class ThaiIDCardReader {
  static const platform = MethodChannel('com.example.thai_idcard');

  Future<Map<String, dynamic>> readCard() async {
    try {
      final result = await platform.invokeMethod('readCard');
      return Map<String, dynamic>.from(result);
    } on PlatformException catch (e) {
      throw Exception('Failed to read card: ${e.message}');
    }
  }
}
```

**Platform-specific:**
- **Android:** Use Kotlin/Java with javax.smartcardio or native ACS SDK
- **iOS:** Use Swift with CryptoTokenKit
- **Desktop:** Call Python pythaiidcard via Process or embed via platform channels

### Approach 4: FFI (Foreign Function Interface)
**Recommended for:** High-performance, C-based integration

**Pros:**
- Synchronous calls (better performance)
- Direct C library access
- Cross-platform if using portable C library
- Lower overhead than platform channels

**Cons:**
- Requires C/C++ development
- More complex setup
- Need to manage memory manually
- Platform-specific compilation

**Implementation Strategy:**
1. Create C wrapper around PC/SC Lite native library
2. Implement Thai ID card reading logic in C
3. Use dart:ffi to call C functions

**Example:**
```dart
import 'dart:ffi' as ffi;

// C function signatures
typedef ReadCardNative = ffi.Pointer<Utf8> Function();
typedef ReadCardDart = ffi.Pointer<Utf8> Function();

class ThaiIDCardReaderFFI {
  late ffi.DynamicLibrary _lib;
  late ReadCardDart _readCard;

  ThaiIDCardReaderFFI() {
    _lib = ffi.DynamicLibrary.open('libthaiidcard.so');
    _readCard = _lib.lookup<ffi.NativeFunction<ReadCardNative>>('read_card')
        .asFunction<ReadCardDart>();
  }

  String readCard() {
    final result = _readCard();
    return result.toDartString();
  }
}
```

### Approach 5: NFC-Based Mobile Implementation
**Recommended for:** Modern mobile apps (newer Thai ID cards with NFC)

**Pros:**
- No external hardware required
- Better user experience on mobile
- Cross-platform (Android/iOS)
- Growing adoption of NFC-enabled Thai ID cards

**Cons:**
- Only works with NFC-enabled Thai ID cards
- Requires NFC permission setup
- Different command flow than PC/SC
- Limited to newer cards

**Implementation:**
```dart
import 'package:flutter_nfc_kit/flutter_nfc_kit.dart';

class ThaiIDCardNFCReader {
  Future<ThaiIDCard> readCard() async {
    // Start NFC session
    var tag = await FlutterNfcKit.poll(
      timeout: Duration(seconds: 10),
      iosMultipleTagMessage: "Multiple cards detected",
      iosAlertMessage: "Hold your Thai ID card near iPhone"
    );

    // Send SELECT APPLET command
    final selectApdu = [0x00, 0xA4, 0x04, 0x00, 0x08,
                        0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01];
    var response = await FlutterNfcKit.transceive(selectApdu);

    // Read data fields
    final cidApdu = [0x80, 0xB0, 0x00, 0x04, 0x02, 0x00, 0x0D];
    var cidResponse = await FlutterNfcKit.transceive(cidApdu);

    // ... more field reading

    await FlutterNfcKit.finish(iosAlertMessage: "Success");

    return ThaiIDCard.fromNfcData(cidResponse, ...);
  }
}
```

---

## Recommended Implementation Strategy

### Phase 1: Quick Validation (Android Only)
**Goal:** Prove concept with minimal effort

1. Use `thai_idcard_reader_flutter` package
2. Build simple Flutter Android app
3. Test with ACS ACR39U reader
4. Validate data extraction matches pythaiidcard

**Effort:** 1-2 days
**Platforms:** Android only

### Phase 2: Desktop Cross-Platform
**Goal:** Bring to Windows/macOS/Linux

1. Use `flutter_pcsc` package
2. Port APDU commands from pythaiidcard
3. Implement ThaiIDCard model in Dart
4. Add photo extraction (20-part JPEG)
5. Handle ATR detection for GET RESPONSE commands

**Effort:** 1-2 weeks
**Platforms:** Windows, macOS, Linux

### Phase 3: iOS/Mobile Support
**Goal:** Full mobile coverage

**Option A - NFC Route:**
1. Use `flutter_nfc_kit`
2. Implement NFC-based reading
3. Test with NFC-enabled Thai ID cards

**Option B - USB Reader Route:**
1. Use `ccid` package for iOS
2. Requires MFi-certified smartcard reader
3. More complex but works with all Thai ID cards

**Effort:** 2-3 weeks
**Platforms:** iOS, Android (NFC)

### Phase 4: Unified Package
**Goal:** Single package supporting all platforms

1. Create unified API surface
2. Platform-specific implementations behind abstraction
3. Comprehensive documentation
4. Example apps for each platform
5. Publish to pub.dev

**Effort:** 3-4 weeks
**Result:** Production-ready Flutter package

---

## Technical Considerations

### APDU Command Compatibility
The APDU commands from pythaiidcard should work directly in Flutter:

```dart
// From pythaiidcard/constants.py
class CardCommands {
  // SELECT APPLET (must return 61 0A or 90 00)
  static const selectApplet = [
    0x00, 0xA4, 0x04, 0x00, 0x08,
    0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01
  ];

  // Read CID (13 bytes)
  static const readCid = [0x80, 0xB0, 0x00, 0x04, 0x02, 0x00, 0x0D];

  // Photo parts (20 commands for 255 bytes each)
  static const readPhoto1 = [0x80, 0xB0, 0x01, 0x7B, 0x02, 0x00, 0xFF];
  // ... through readPhoto20
}
```

### Response Status Handling
**Critical:** Must handle both `90 00` AND `61 XX` as success:

```dart
bool isSuccess(List<int> response) {
  if (response.length < 2) return false;

  // SW1 = 0x90, SW2 = 0x00 (success)
  if (response[response.length - 2] == 0x90 &&
      response[response.length - 1] == 0x00) {
    return true;
  }

  // SW1 = 0x61, SW2 = XX (success with more data)
  if (response[response.length - 2] == 0x61) {
    return true;
  }

  return false;
}
```

### ATR Detection
Different readers return different ATR values:

```dart
List<int> getReadResponseCommand(String atr) {
  // ATR starting with 3B 67 uses different GET RESPONSE
  if (atr.startsWith('3B67')) {
    return [0x00, 0xC0, 0x00, 0x01]; // Special case
  }
  return [0x00, 0xC0, 0x00, 0x00]; // Standard
}
```

### Date Conversion
Thai ID cards use Buddhist Era (BE):

```dart
DateTime parseThaiDate(String thaiDate) {
  // Format: YYYYMMDD in Buddhist Era
  final year = int.parse(thaiDate.substring(0, 4)) - 543; // Convert to Gregorian
  final month = int.parse(thaiDate.substring(4, 6));
  final day = int.parse(thaiDate.substring(6, 8));
  return DateTime(year, month, day);
}
```

### Photo Assembly
Photos are 20 parts of 255 bytes each:

```dart
Future<Uint8List> readPhoto(Card card, {Function(int)? onProgress}) async {
  final buffer = BytesBuilder();

  for (int i = 1; i <= 20; i++) {
    final photoCommand = getPhotoCommand(i);
    final response = await card.transmit(photoCommand);

    // Remove status bytes (last 2 bytes)
    buffer.add(response.sublist(0, response.length - 2));

    if (onProgress != null) {
      onProgress((i * 100) ~/ 20); // Progress percentage
    }
  }

  return buffer.toBytes(); // Complete JPEG
}
```

---

## Comparison Matrix

| Approach | Platforms | Effort | Performance | Maintenance | Hardware |
|----------|-----------|--------|-------------|-------------|----------|
| **thai_idcard_reader_flutter** | Android | Low | Good | Unknown | ACS only |
| **flutter_pcsc** | Desktop (Win/Mac/Linux) | Medium | Good | Active | Any PC/SC |
| **Platform Channels** | All | High | Medium | High | Any |
| **FFI** | All (with work) | High | Excellent | Medium | Any |
| **NFC (flutter_nfc_kit)** | Mobile (Android/iOS) | Medium | Good | Active | Built-in NFC |
| **ccid** | iOS/Mac/Linux | Medium | Good | Active | MFi or Mac |

---

## Licensing Considerations

- **flutter_pcsc:** MIT License (permissive)
- **flutter_nfc_kit:** Check package license (typically MIT/BSD)
- **PC/SC Lite:** BSD-like license (permissive)
- **pythaiidcard:** Check your current license

Ensure any Flutter package you create is compatible with these licenses.

---

## Recommended Path Forward

### For Quick Prototype
1. Use `thai_idcard_reader_flutter` on Android
2. Validate functionality matches pythaiidcard
3. Assess if it meets your needs

### For Production Desktop App
1. Use `flutter_pcsc` package
2. Port pythaiidcard APDU logic to Dart
3. Create comprehensive Dart models
4. Add extensive error handling
5. Build example apps

### For Production Mobile App
1. Use `flutter_nfc_kit` for NFC approach
2. Test with newer Thai ID cards with NFC
3. Implement same data models as desktop
4. Consider fallback to USB readers via Platform Channels

### For Maximum Coverage
1. Create abstraction layer (`ThaiIDCardReader` interface)
2. Multiple implementations:
   - `ThaiIDCardReaderPCSC` (desktop via flutter_pcsc)
   - `ThaiIDCardReaderNFC` (mobile via flutter_nfc_kit)
   - `ThaiIDCardReaderACS` (Android via thai_idcard_reader_flutter)
3. Factory pattern to select appropriate implementation
4. Shared data models and validation

---

## Example Project Structure

```
thai_id_card_flutter/
├── lib/
│   ├── src/
│   │   ├── models/
│   │   │   ├── thai_id_card.dart         # Main data model
│   │   │   └── reader_info.dart          # Reader information
│   │   ├── constants/
│   │   │   ├── apdu_commands.dart        # All APDU commands
│   │   │   └── response_status.dart      # Status code validation
│   │   ├── readers/
│   │   │   ├── reader_interface.dart     # Abstract interface
│   │   │   ├── pcsc_reader.dart          # Desktop (flutter_pcsc)
│   │   │   ├── nfc_reader.dart           # Mobile (flutter_nfc_kit)
│   │   │   └── acs_reader.dart           # Android (thai_idcard_reader_flutter)
│   │   ├── utils/
│   │   │   ├── date_converter.dart       # BE to Gregorian
│   │   │   ├── cid_validator.dart        # CID checksum
│   │   │   └── encoding_utils.dart       # TIS-620 handling
│   │   └── exceptions/
│   │       └── exceptions.dart           # Exception hierarchy
│   └── thai_id_card_flutter.dart         # Main export
├── example/
│   ├── desktop_example/                  # Desktop demo
│   ├── mobile_example/                   # Mobile demo
│   └── web_example/                      # Web demo (if applicable)
├── test/
│   ├── models_test.dart
│   ├── validators_test.dart
│   └── reader_test.dart
├── pubspec.yaml
└── README.md
```

---

## Next Steps

1. **Decide on target platforms:**
   - Android only → Use `thai_idcard_reader_flutter`
   - Desktop → Use `flutter_pcsc`
   - Mobile → Use `flutter_nfc_kit`
   - All platforms → Hybrid approach

2. **Create proof of concept:**
   - Build minimal Flutter app
   - Read one Thai ID card
   - Validate data against pythaiidcard

3. **Evaluate existing solutions:**
   - Test `thai_idcard_reader_flutter` if targeting Android
   - Assess if it has all features you need

4. **Plan full implementation:**
   - Port APDU commands
   - Implement data models
   - Add photo extraction
   - Create comprehensive tests

5. **Consider publishing:**
   - If you create a comprehensive solution
   - Contribute back to Flutter community
   - Many developers need Thai ID card reading

---

## Conclusion

**There ARE existing Flutter solutions**, particularly:
- `thai_idcard_reader_flutter` for Android + ACS readers
- `flutter_pcsc` for desktop PC/SC readers
- `flutter_nfc_kit` for NFC-based mobile reading

**However, none provide the same comprehensive cross-platform support as pythaiidcard.** Creating a unified Flutter package that works across desktop and mobile with full feature parity would be a valuable contribution to the Flutter ecosystem.

The **recommended approach** depends on your specific needs:
- **Quick Android solution:** Use existing `thai_idcard_reader_flutter`
- **Desktop application:** Build on `flutter_pcsc`
- **Modern mobile app:** Use `flutter_nfc_kit` with NFC
- **Comprehensive solution:** Create unified package with platform-specific implementations

All approaches are technically feasible, and the APDU commands from pythaiidcard can be directly ported to Dart with minimal modification.
