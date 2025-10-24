# Thai ID Card Reader Test - Flutter/CCID

**Purpose:** Proof-of-concept Flutter application to test reading Thai National ID cards using the `ccid` package.

This is a minimal test application created to validate the [`ccid`](https://pub.dev/packages/ccid) Flutter package for reading Thai ID cards via smartcard readers, as part of research for creating a Flutter version of the [pythaiidcard](https://github.com/ninyawee/pythaiidcard) library.

## About CCID Package

- **Package:** `ccid` v0.1.8
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

✅ **Already Configured:**
- Smartcard entitlement in `ios/Runner/Runner.entitlements`
- Export options in `ios/Runner/ExportOptions.plist`
- GitHub Actions workflow in `.github/workflows/ios-build.yml`
- Fastlane automation in `ios/fastlane/`

**To enable cloud builds:**
1. Configure GitHub secrets (see `CLOUD_BUILD_SETUP.md`)
2. Update Team ID in `ios/Runner/ExportOptions.plist`
3. Update provisioning profile name in `ExportOptions.plist`

**Optional:**
- Update `ios/Runner/Info.plist` with supported reader AIDs (if needed)

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

### On iOS Device (macOS)
```bash
# Requires Xcode and provisioning profile
flutter run
```

### On iOS Device from Linux

Since iOS builds require Xcode (macOS only), there are several approaches to test on iPhone from a Linux development machine:

#### Option 1: Cloud CI/CD Build (Recommended)

Use GitHub Actions to build iOS app remotely, then install on your iPhone:

```bash
# 1. Push code to GitHub
git push origin master

# 2. GitHub Actions builds iOS IPA automatically (see .github/workflows/ios-build.yml)
# 3. Download IPA artifact from GitHub Actions artifacts
# 4. Install IPA on iPhone using one of these methods:

# Method A: Using iOS App Signer + Diawi (easiest)
# - Upload IPA to https://www.diawi.com/
# - Open link on iPhone to install

# Method B: Using Apple Configurator 2 (on a Mac you have access to)
# - Connect iPhone to Mac
# - Open Apple Configurator 2
# - Drag IPA to device

# Method C: Using Xcode (on a Mac you have access to)
# - Connect iPhone to Mac
# - Open Xcode → Window → Devices and Simulators
# - Drag IPA to device
```

**Setup Requirements:**
1. Configure GitHub secrets (see `CLOUD_BUILD_SETUP.md`)
2. Valid Apple Developer account with provisioning profile
3. Device UDID registered in provisioning profile

**Pros:**
- ✅ No Mac required locally
- ✅ Automated builds on every push
- ✅ Free for public repositories (GitHub Actions)

**Cons:**
- ❌ No live debugging from Linux
- ❌ Slower iteration (commit → build → download → install)
- ❌ Requires initial setup of code signing

#### Option 2: Remote Mac Access

Access a remote Mac for building and deployment:

**Cloud Mac Services:**
```bash
# MacStadium, AWS EC2 Mac instances, or MacinCloud

# SSH into remote Mac
ssh user@remote-mac.example.com

# Clone repository
git clone https://github.com/your-org/thai_idcard_reader_test.git
cd thai_idcard_reader_test

# Build and install
flutter build ios
# Then deploy to connected iPhone or TestFlight
```

**Self-hosted Mac:**
```bash
# If you have access to a Mac on your network

# Enable Remote Login on Mac (System Settings → Sharing → Remote Login)

# SSH from Linux
ssh your-user@mac-ip-address

# Use same build commands as above
```

**Pros:**
- ✅ Full Xcode access
- ✅ Can debug using Xcode remotely
- ✅ Faster iteration than CI/CD

**Cons:**
- ❌ Requires paid Mac access or own Mac
- ❌ Network latency for remote access

#### Option 3: Wireless Debugging (Limited)

Use Flutter's wireless debugging if you already have the app installed:

```bash
# 1. First-time setup requires macOS to install the app
# 2. Once installed, you can use wireless debugging from Linux

# Enable wireless debugging on iPhone:
# - Connect iPhone to Mac with cable once
# - Open Xcode → Window → Devices and Simulators
# - Select iPhone → Check "Connect via network"

# From Linux (requires mdns/avahi for device discovery)
flutter devices  # Should show iPhone over network

# Run app wirelessly
flutter run -d <iphone-device-id>

# Note: Hot reload works, but you cannot install a new app from Linux
```

**Pros:**
- ✅ Hot reload works from Linux
- ✅ No cable required after initial setup

**Cons:**
- ❌ Initial app installation requires Mac
- ❌ Device discovery can be unreliable
- ❌ Cannot install new builds from Linux

#### Option 4: Hybrid Development Workflow (Practical)

Combine approaches for efficient development:

```bash
# Day-to-day development on Android (from Linux)
flutter run  # Test on Android device connected via USB

# Periodic iOS testing via CI/CD
git commit -m "feat: Add card reading UI"
git push origin feature/card-reading
# GitHub Actions builds iOS automatically
# Download and test on iPhone weekly or before releases

# Critical iOS debugging
# - SSH into remote Mac or use cloud Mac service
# - Use Xcode for platform-specific issues
```

**Workflow:**
1. Develop primarily on Android (USB debugging from Linux)
2. Push to GitHub for automated iOS builds
3. Test iOS builds periodically
4. Use remote Mac only for iOS-specific debugging

**Pros:**
- ✅ Fast iteration on Android
- ✅ Regular iOS validation via CI/CD
- ✅ Cost-effective (minimal Mac usage)

**Cons:**
- ❌ Potential iOS-specific bugs discovered late

#### Comparison Table

| Method | Mac Required | Live Debugging | Build Speed | Cost |
|--------|--------------|----------------|-------------|------|
| **Cloud CI/CD** | No (GitHub Actions) | No | Slow (5-10 min) | Free (public repos) |
| **Remote Mac** | Yes (cloud/network) | Yes (via SSH) | Medium | $$-$$$ |
| **Wireless Debug** | Yes (one-time) | Limited | Fast | Free (if Mac available) |
| **Hybrid Workflow** | No (for development) | No | Fast (Android) | Free |

#### Recommended Approach

For this project (Thai ID Card Reader Test):

1. **Primary development:** Use Android device on Linux
   - Both Android and iOS use the same `ccid` package
   - APDU commands are identical across platforms
   - UI code is shared (Flutter)

2. **iOS validation:** Use GitHub Actions CI/CD
   - Automated builds on every push
   - Download IPA and test on iPhone periodically
   - No local Mac required

3. **iOS debugging:** Use remote Mac only if needed
   - For platform-specific issues
   - For Xcode Instruments profiling
   - For smartcard reader compatibility testing

**Testing iPhone with smartcard reader from Linux:**
```bash
# 1. Develop and test APDU logic on Android first
flutter run  # Android device via USB

# 2. Verify APDU commands work with Android + USB OTG reader
# 3. Push code to trigger iOS build
git add . && git commit -m "feat: Implement card reading" && git push

# 4. Wait for GitHub Actions build (~10 minutes)
# 5. Download IPA from GitHub Actions artifacts
# 6. Install IPA on iPhone using Diawi or Apple Configurator
# 7. Test with MFi-certified Lightning smartcard reader
# 8. Compare results with Android to ensure parity
```

This workflow allows **full iOS testing from a Linux machine** without owning a Mac!

## Project Structure

```
thai_idcard_reader_test/
├── lib/
│   └── main.dart          # Minimal UI with read button
├── android/               # Android platform code
├── ios/                   # iOS platform code
│   ├── fastlane/         # Fastlane automation for iOS builds
│   └── Runner/
│       ├── Runner.entitlements   # Smartcard capability
│       └── ExportOptions.plist   # IPA export configuration
├── .github/
│   └── workflows/
│       └── ios-build.yml # GitHub Actions CI/CD for iOS
├── pubspec.yaml          # Dependencies (includes ccid: ^0.1.8)
├── CLAUDE.md             # Development guide for Claude Code
├── CLOUD_BUILD_SETUP.md  # iOS cloud build setup instructions
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

- **Parent project:** [pythaiidcard](../../README.md)
- **Flutter library research:** [notes/FLUTTER_LIBRARY_RESEARCH.md](../../notes/FLUTTER_LIBRARY_RESEARCH.md)
- **iOS cloud build setup:** [CLOUD_BUILD_SETUP.md](CLOUD_BUILD_SETUP.md) - Complete guide for GitHub Actions and Fastlane
- **Development guide:** [CLAUDE.md](CLAUDE.md) - Commands and architecture reference
- **Fastlane documentation:** [ios/fastlane/README.md](ios/fastlane/README.md)
- **CCID package:** https://pub.dev/packages/ccid

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
