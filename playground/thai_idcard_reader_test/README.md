# Thai ID Card Reader Test - Flutter/CCID

**Purpose:** Proof-of-concept Flutter application to test reading Thai National ID cards using the `ccid` package.

This is a minimal test application created to validate the [`ccid`](https://pub.dev/packages/ccid) Flutter package for reading Thai ID cards via smartcard readers, as part of research for creating a Flutter version of the [pythaiidcard](https://github.com/ninyawee/pythaiidcard) library.

## About CCID Package

- **Package:** `ccid` v0.3.0
- **Purpose:** Smart card reading using CCID protocol with PC/SC-like APIs
- **Platform Support:**
  - iOS ✅ (iOS 13.0+, requires MFi-certified smartcard reader)
  - Android ✅ (requires USB OTG smartcard reader)
  - macOS ✅ (built-in CryptoTokenKit support)
  - Linux ❌ (not included in this test)
  - Windows ❌ (not supported by ccid package)

## Hardware Requirements

**Critical:** Thai National ID cards do NOT support NFC. You must have an external smartcard reader:

### Recommended Readers
- **For Android:** USB OTG smartcard readers
  - ACS ACR39U-NF PocketMate II (USB Type-C)
  - ACS ACR122U (USB-A with OTG adapter)
- **For iOS:** MFi-certified Lightning/USB-C smartcard readers
  - Identiv uTrust 3700 F
  - Feitian iR301-U
  - ACS CryptoMate series (MFi-certified models)

## Setup

### 1. Install Dependencies

```bash
# From this directory
flutter pub get
```

### 2. Platform-Specific Configuration

#### iOS Setup
1. Add smartcard entitlement to `ios/Runner/Runner.entitlements`:
   ```xml
   <key>com.apple.security.smartcard</key>
   <true/>
   ```

2. Update `ios/Runner/Info.plist` with supported reader AIDs (if needed)

#### Android Setup
1. Add USB host permissions to `android/app/src/main/AndroidManifest.xml`:
   ```xml
   <uses-feature android:name="android.hardware.usb.host" />
   <uses-permission android:name="android.permission.USB_PERMISSION" />
   ```

2. Add USB device filter for your smartcard reader (optional but recommended)

## Running the Application

### On Android Device
```bash
# Ensure device is connected via ADB
flutter run

# Or build APK
flutter build apk
```

### On iOS Device
```bash
# Requires Xcode and provisioning profile
flutter run
```

## Project Structure

```
thai_idcard_reader_test/
├── lib/
│   └── main.dart          # Minimal UI with read button
├── android/               # Android platform code
├── ios/                   # iOS platform code
├── pubspec.yaml          # Dependencies (includes ccid: ^0.3.0)
└── README.md             # This file
```

## Expected Implementation

This test app will:
1. Detect connected smartcard readers
2. Connect to Thai ID card when inserted
3. Send SELECT APPLET command (`A0 00 00 00 54 48 00 01`)
4. Read basic card fields (CID, name, date of birth, etc.)
5. Display results in simple text UI

## Thai ID Card Technical Details

### APDU Command Flow
1. **SELECT APPLET:** `00 A4 04 00 08 A0 00 00 00 54 48 00 01`
   - Expected response: `61 0A` (success with 10 bytes) or `90 00` (success)
2. **Read CID:** `80 B0 00 04 02 00 0D` + GET RESPONSE
3. **Read other fields:** Similar pattern with different offsets

### Data Fields Available
- CID (Citizen ID): 13 digits
- Thai Name (Full name)
- English Name (Full name)
- Date of Birth (Buddhist Era format)
- Gender
- Address
- Issue Date / Expiry Date
- Photo (5,100 bytes JPEG in 20 parts)

## Related Documentation

- Parent project: [pythaiidcard](../../README.md)
- Flutter library research: [notes/FLUTTER_LIBRARY_RESEARCH.md](../../notes/FLUTTER_LIBRARY_RESEARCH.md)
- CCID package documentation: https://pub.dev/packages/ccid

## Testing Checklist

- [ ] Install dependencies (`flutter pub get`)
- [ ] Configure platform-specific permissions
- [ ] Connect smartcard reader to device
- [ ] Insert Thai ID card
- [ ] Run application
- [ ] Press "Read Card" button
- [ ] Verify CID and basic data displays correctly
- [ ] Compare output with pythaiidcard Python library

## Known Limitations

1. **No NFC support** - Thai ID cards do not have NFC capability
2. **Requires external reader** - Cannot use built-in phone hardware
3. **Platform-specific entitlements** - iOS requires MFi-certified readers and proper entitlements
4. **Minimal UI** - This is a proof-of-concept, not production-ready

## Next Steps

If this test is successful:
1. Port full APDU command set from pythaiidcard
2. Implement comprehensive data models
3. Add photo extraction (20-part JPEG assembly)
4. Create production-ready UI
5. Handle all error cases
6. Add comprehensive tests

## License

This test application is part of the pythaiidcard project research.
