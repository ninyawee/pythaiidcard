# iOS Cloud Build Setup Guide

This guide walks through setting up automated iOS builds using GitHub Actions and Fastlane.

## Quick Start

The project is pre-configured with:
- ✅ GitHub Actions workflow (`.github/workflows/ios-build.yml`)
- ✅ Fastlane configuration (`ios/fastlane/`)
- ✅ iOS entitlements file with smartcard capability
- ✅ Export options template

**What you need to configure:**
1. Apple Developer account credentials
2. Code signing certificates and provisioning profiles (for release builds only)
3. GitHub repository secrets (for CI/CD)

## GitHub Actions Workflow

### Automatic Triggers

The workflow runs automatically on:
- **Push** to `master` or `main` branches → Release build with code signing
- **Pull requests** to `master` or `main` → Debug build (no code signing)
- **Push** to `feature/**` or `release/**` branches → Debug build

### Manual Triggers

You can manually trigger builds from GitHub:
1. Go to **Actions** tab in your repository
2. Select **iOS Build** workflow
3. Click **Run workflow**
4. Choose build type: `debug` or `release`

### Build Types

**Debug Build (No Code Signing):**
- Runs on pull requests and feature branches
- Uses `--no-codesign` flag
- Faster builds
- Artifacts retained for 7 days
- No secrets required

**Release Build (With Code Signing):**
- Runs on push to `master`/`main` or manual trigger with `release` option
- Requires code signing setup
- Creates signed IPA file
- Artifacts retained for 30 days
- Requires GitHub secrets

## Code Signing Setup

### Prerequisites

1. **Apple Developer Account** (paid, $99/year)
2. **Mac with Xcode** (for initial certificate generation)
3. **Git repository access** (for storing workflow secrets)

### Step 1: Generate Certificates

**Option A: Using Xcode (Easiest)**

1. Open Xcode
2. Go to **Xcode → Settings → Accounts**
3. Add your Apple ID
4. Select your team → Click **Manage Certificates**
5. Click **+** → **iOS Development** (or **iOS Distribution** for App Store)
6. Certificate is automatically created and installed

**Option B: Using Apple Developer Portal**

1. Go to [Apple Developer Portal](https://developer.apple.com/account/resources/certificates)
2. Click **+** to create new certificate
3. Choose **iOS App Development** or **iOS Distribution**
4. Generate CSR (Certificate Signing Request):
   ```bash
   # Create CSR on Mac
   # Open Keychain Access → Certificate Assistant → Request a Certificate from a Certificate Authority
   # Save as .certSigningRequest file
   ```
5. Upload CSR and download certificate (.cer)
6. Double-click .cer to install in Keychain

### Step 2: Export Certificate as .p12

1. Open **Keychain Access**
2. Select **My Certificates**
3. Find your iOS Development certificate
4. Right-click → **Export "iPhone Developer: Your Name"**
5. Save as `.p12` file
6. **Set a password** (you'll need this for GitHub secrets)
7. Keep this file secure!

### Step 3: Create Provisioning Profile

1. Go to [Apple Developer Portal → Profiles](https://developer.apple.com/account/resources/profiles)
2. Click **+** to create new profile
3. Choose profile type:
   - **iOS App Development**: For development and testing
   - **App Store**: For App Store distribution
4. Select your App ID (create one if needed):
   - Bundle ID: `com.example.thaiIdcardReaderTest`
   - Enable **Personal VPN** capability (for smartcard access)
5. Select certificate (from Step 1)
6. Select devices (for development profiles)
7. Download `.mobileprovision` file

### Step 4: Update Export Options

Edit `ios/Runner/ExportOptions.plist`:

```xml
<key>teamID</key>
<string>YOUR_TEAM_ID</string>  <!-- Replace with your 10-character Team ID -->

<key>provisioningProfiles</key>
<dict>
    <key>com.example.thaiIdcardReaderTest</key>
    <string>Your Provisioning Profile Name</string>  <!-- Replace -->
</dict>
```

**Find your Team ID:**
- Apple Developer Portal → Membership → Team ID
- Or in Xcode: Settings → Accounts → Team Name (shows Team ID)

### Step 5: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **New repository secret**
4. Add the following secrets:

#### Required Secrets

**`IOS_CERTIFICATE_BASE64`**
```bash
# On macOS
base64 -i certificate.p12 | pbcopy

# On Linux
base64 -w 0 certificate.p12

# Paste the output into GitHub secret
```

**`IOS_CERTIFICATE_PASSWORD`**
- The password you set when exporting the .p12 file in Step 2

**`IOS_PROVISIONING_PROFILE_BASE64`**
```bash
# On macOS
base64 -i profile.mobileprovision | pbcopy

# On Linux
base64 -w 0 profile.mobileprovision

# Paste the output into GitHub secret
```

**`KEYCHAIN_PASSWORD`**
- Any secure random string (used for temporary keychain in CI)
- Example: `K3ych@1n_P@ssw0rd_2024`
- This is NOT your Apple ID password

### Step 6: Test the Workflow

1. **Commit and push** changes to `master` branch
2. Go to **Actions** tab in GitHub
3. Watch the workflow run
4. Check for errors in build logs
5. Download IPA artifact when build completes

## Using Fastlane Locally

### Install Fastlane

```bash
# Using Homebrew (recommended for macOS)
brew install fastlane

# Or using RubyGems
sudo gem install fastlane
```

### Configure Environment

Create `ios/fastlane/.env` (not committed to git):

```bash
# Apple Developer Account
APPLE_ID=your-apple-id@example.com
TEAM_ID=YOUR_TEAM_ID
APP_IDENTIFIER=com.example.thaiIdcardReaderTest

# Provisioning Profile
PROVISIONING_PROFILE_NAME=YourProvisioningProfileName

# Code Signing (for local builds)
IOS_CERTIFICATE_PATH=/path/to/certificate.p12
IOS_CERTIFICATE_PASSWORD=your-p12-password
IOS_PROVISIONING_PROFILE_PATH=/path/to/profile.mobileprovision
```

### Update Fastlane Configuration

Edit `ios/fastlane/Appfile`:

```ruby
apple_id(ENV["APPLE_ID"] || "your-apple-id@example.com")
team_id(ENV["TEAM_ID"] || "YOUR_TEAM_ID")
app_identifier(ENV["APP_IDENTIFIER"] || "com.example.thaiIdcardReaderTest")
```

### Build Locally

```bash
cd ios

# Development build (no code signing)
fastlane build_dev

# Release build (with code signing)
fastlane build_release

# Upload to TestFlight
fastlane beta

# Run tests
fastlane test
```

## Advanced: Fastlane Match (Recommended for Teams)

Fastlane Match stores certificates and provisioning profiles in a private git repository, making it easy to share across team members and CI/CD.

### Setup Match

1. **Create a private git repository** for certificates:
   ```bash
   # Example: github.com/your-org/ios-certificates
   ```

2. **Initialize Match:**
   ```bash
   cd ios
   fastlane match init
   # Choose 'git' and enter repository URL
   ```

3. **Generate certificates:**
   ```bash
   # Development certificates
   fastlane match development

   # App Store certificates
   fastlane match appstore
   ```

4. **Update Fastfile:**

   Uncomment the `match` section in `ios/fastlane/Fastfile`:
   ```ruby
   lane :setup_code_signing do
     match(
       type: "development",
       readonly: ENV['CI'],
       app_identifier: "com.example.thaiIdcardReaderTest"
     )
   end
   ```

5. **Add Match secrets to GitHub:**
   - `MATCH_GIT_URL`: Repository URL
   - `MATCH_PASSWORD`: Encryption password for certificates

### Benefits of Match

- ✅ Single source of truth for certificates
- ✅ Easy team collaboration
- ✅ Automatic certificate renewal
- ✅ Works seamlessly with CI/CD
- ✅ No manual .p12 export needed

## Troubleshooting

### "No signing certificate found"

**Solution:**
1. Verify certificate is not expired (check Apple Developer Portal)
2. Re-export .p12 with correct password
3. Ensure GitHub secret `IOS_CERTIFICATE_BASE64` is set correctly
4. Check GitHub Actions logs for certificate import errors

### "Provisioning profile doesn't match"

**Solution:**
1. Verify App ID in provisioning profile matches `com.example.thaiIdcardReaderTest`
2. Ensure provisioning profile includes your certificate
3. Download fresh provisioning profile from Apple Developer Portal
4. Update `ExportOptions.plist` with correct profile name

### "Xcode version mismatch"

**Solution:**
1. Update `XCODE_VERSION` in `.github/workflows/ios-build.yml`
2. Check available Xcode versions on GitHub runners:
   - [macOS 14 runner](https://github.com/actions/runner-images/blob/main/images/macos/macos-14-Readme.md)

### "Pod install fails"

**Solution:**
```bash
cd ios
pod repo update
pod install --repo-update
```

### "Build timeout"

**Solution:**
1. Increase `timeout-minutes` in workflow file
2. Enable caching for Flutter and CocoaPods
3. Consider using Fastlane Match to speed up code signing

## Build Artifacts

### Debug Builds
- **Location:** `build/ios/iphoneos/Runner.app`
- **Retention:** 7 days
- **Installation:** Cannot be installed on physical devices (no code signing)
- **Purpose:** CI/CD validation and testing

### Release Builds
- **Location:** `$RUNNER_TEMP/build/*.ipa`
- **Retention:** 30 days
- **Installation:** Can be installed on registered devices
- **Purpose:** Distribution via TestFlight or App Store

### Downloading Artifacts

1. Go to **Actions** tab in GitHub
2. Click on completed workflow run
3. Scroll to **Artifacts** section
4. Download IPA file
5. Install using Xcode or TestFlight

## Security Best Practices

1. ✅ **Never commit** `.p12` files, `.mobileprovision` files, or passwords
2. ✅ **Use GitHub secrets** for all sensitive data
3. ✅ **Rotate certificates** annually (Apple requirement)
4. ✅ **Use Fastlane Match** for team environments
5. ✅ **Enable 2FA** on Apple Developer account
6. ✅ **Limit repository access** to necessary team members
7. ✅ **Audit workflow logs** for security issues
8. ✅ **Use environment-specific** provisioning profiles

## Resources

- [GitHub Actions for iOS](https://docs.github.com/en/actions/deployment/deploying-xcode-applications)
- [Fastlane Documentation](https://docs.fastlane.tools/)
- [Fastlane Match](https://docs.fastlane.tools/actions/match/)
- [Apple Developer Portal](https://developer.apple.com/account/)
- [Flutter iOS Deployment](https://docs.flutter.dev/deployment/ios)
- [Code Signing Guide](https://developer.apple.com/support/code-signing/)

## Support

For build issues:
1. Check GitHub Actions logs
2. Review Fastlane logs in `ios/fastlane/logs/`
3. Run `flutter doctor -v` to verify environment
4. Test build locally before pushing to CI

For code signing issues:
1. Verify certificate in Keychain Access
2. Check provisioning profile validity in Xcode
3. Ensure App ID capabilities match (Personal VPN for smartcard)
4. Review Apple Developer Portal for certificate status
