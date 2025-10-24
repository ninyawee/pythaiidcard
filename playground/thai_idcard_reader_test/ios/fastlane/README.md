# Fastlane iOS Automation

This directory contains Fastlane configuration for automating iOS builds, testing, and deployment.

## Prerequisites

1. **Install Fastlane:**
   ```bash
   # Using RubyGems
   sudo gem install fastlane

   # Or using Homebrew
   brew install fastlane
   ```

2. **Install Flutter:**
   - Ensure Flutter is installed and in your PATH
   - Version 3.24.0 or later

3. **Xcode Setup:**
   - Xcode 15.0 or later
   - Valid Apple Developer account
   - Code signing certificates and provisioning profiles

## Configuration

### Environment Variables

Create a `.env` file in the `ios/fastlane/` directory (not committed to git):

```bash
# Apple Developer Account
APPLE_ID=your-apple-id@example.com
TEAM_ID=YOUR_TEAM_ID
APP_IDENTIFIER=com.example.thaiIdcardReaderTest

# Code Signing (for CI/CD)
IOS_CERTIFICATE_PATH=/path/to/certificate.p12
IOS_CERTIFICATE_PASSWORD=your-certificate-password
IOS_PROVISIONING_PROFILE_PATH=/path/to/profile.mobileprovision
PROVISIONING_PROFILE_NAME=YourProvisioningProfileName

# Fastlane Match (if using)
MATCH_GIT_URL=git@github.com:your-org/certificates.git
MATCH_PASSWORD=your-match-password
```

### Export Options

Update `ios/Runner/ExportOptions.plist`:
- Replace `YOUR_TEAM_ID` with your Apple Developer Team ID
- Replace `YOUR_PROVISIONING_PROFILE_NAME` with your provisioning profile name
- Adjust `method` based on distribution type:
  - `development`: For local development and testing
  - `ad-hoc`: For ad-hoc distribution
  - `enterprise`: For enterprise distribution
  - `app-store`: For App Store submission

## Available Lanes

### Development

```bash
# Build iOS app for development (debug, no code signing)
cd ios
fastlane build_dev

# Run tests and code analysis
fastlane test

# Update dependencies
fastlane update_deps

# Clean build artifacts
fastlane clean

# Run linting and formatting
fastlane lint
```

### Release Builds

```bash
# Build release IPA (requires code signing)
fastlane build_release

# Build and upload to TestFlight
fastlane beta

# Build and upload to App Store
fastlane release
```

### Code Signing

```bash
# Setup code signing (using Fastlane Match)
fastlane setup_code_signing

# Setup code signing manually (from local certificates)
fastlane setup_certificates cert_path:/path/to/cert.p12 cert_password:password profile_path:/path/to/profile.mobileprovision
```

### Versioning

```bash
# Increment build number
fastlane bump_build

# Set version number
fastlane set_version version:1.0.0
```

### CI/CD

```bash
# CI build (used by GitHub Actions)
fastlane ci_build build_type:debug
fastlane ci_build build_type:release
```

## Code Signing Setup

### Option 1: Manual Code Signing

1. **Export Certificate:**
   ```bash
   # From Keychain Access, export your developer certificate as .p12
   # Store securely and set password
   ```

2. **Download Provisioning Profile:**
   - Go to Apple Developer portal
   - Download provisioning profile
   - Install to `~/Library/MobileDevice/Provisioning Profiles/`

3. **Configure GitHub Secrets** (for CI/CD):
   - `IOS_CERTIFICATE_BASE64`: Base64 encoded .p12 file
     ```bash
     base64 -i certificate.p12 | pbcopy
     ```
   - `IOS_CERTIFICATE_PASSWORD`: Certificate password
   - `IOS_PROVISIONING_PROFILE_BASE64`: Base64 encoded provisioning profile
     ```bash
     base64 -i profile.mobileprovision | pbcopy
     ```
   - `KEYCHAIN_PASSWORD`: Temporary keychain password (any secure string)

### Option 2: Fastlane Match (Recommended for Teams)

1. **Setup Match Repository:**
   ```bash
   fastlane match init
   ```

2. **Generate Certificates:**
   ```bash
   fastlane match development
   fastlane match appstore
   ```

3. **Update Fastfile:**
   - Uncomment the `match` section in `setup_code_signing` lane
   - Configure app identifier and git repository

## GitHub Actions Integration

The project includes a GitHub Actions workflow (`.github/workflows/ios-build.yml`) that:
- Builds iOS app on every push to main branches
- Runs tests and code analysis
- Creates IPA for release builds
- Uploads artifacts

**Workflow Configuration:**
1. Add required secrets to GitHub repository settings
2. Push to `master` or `main` branch to trigger builds
3. Use workflow dispatch for manual builds

## Troubleshooting

### Code Signing Issues

```bash
# List available certificates
security find-identity -v -p codesigning

# List available provisioning profiles
ls ~/Library/MobileDevice/Provisioning\ Profiles/

# Verify Xcode project settings
xcodebuild -showBuildSettings -workspace Runner.xcworkspace -scheme Runner
```

### Build Errors

```bash
# Clean all build artifacts
fastlane clean

# Update CocoaPods
cd ios
pod install --repo-update

# Reset Flutter
cd ..
flutter clean
flutter pub get
```

### Fastlane Issues

```bash
# Update Fastlane
sudo gem update fastlane

# Clear derived data
rm -rf ~/Library/Developer/Xcode/DerivedData

# Reset simulators
xcrun simctl erase all
```

## Resources

- [Fastlane Documentation](https://docs.fastlane.tools/)
- [Flutter iOS Deployment](https://docs.flutter.dev/deployment/ios)
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [Fastlane Match](https://docs.fastlane.tools/actions/match/)

## Support

For issues specific to:
- **Fastlane:** Check logs in `ios/fastlane/logs/`
- **Flutter:** Run `flutter doctor -v`
- **Xcode:** Check build logs in Xcode organizer
