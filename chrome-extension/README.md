# Thai ID Card Reader - Chrome Extension

A Chrome extension that integrates with the Thai ID Card Reader desktop application to automatically fill web forms with data from Thai National ID cards.

## Features

- **Real-time Card Reading**: Connects to your local card reader server via WebSocket
- **Secure Authentication**: Uses passcode-based authentication to protect your data
- **Auto-fill Forms**: Automatically fills PeakAccount and other web forms with card data
- **Copy to Clipboard**: Quickly copy CID, names, or address with one click
- **Download Data**: Export card data as JSON
- **Privacy First**: All data stays on your computer - no cloud storage

## Prerequisites

1. **Desktop Application**: You must have the Thai ID Card Reader desktop application running
2. **Card Reader Hardware**: A PC/SC compatible smart card reader
3. **Thai ID Card**: A valid Thai National ID card

## Installation

### Step 1: Install the Extension

1. Download or clone this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" (toggle in top right)
4. Click "Load unpacked"
5. Select the `chrome-extension` folder from this project

The extension icon should now appear in your Chrome toolbar.

### Step 2: Start the Desktop Application

1. Start the Thai ID Card Reader desktop application
2. The server should start automatically (or click "Start Server" from the tray menu)
3. Verify the server is running on `http://localhost:8765`

### Step 3: Pair the Extension

1. Right-click the desktop application tray icon
2. Select "Extension Pairing & Settings..."
3. Click "Generate New Passcode" (or copy the existing passcode)
4. Copy the generated passcode (10-character alphanumeric code)

5. Click the extension icon in Chrome
6. Paste the passcode into the "Passcode" field
7. Click "Connect"

The status indicator should turn green showing "Connected"

## Usage

### Reading Card Data

1. Insert your Thai ID card into the card reader
2. The extension will automatically detect when a card is read
3. Card data will appear in the extension popup

You can also trigger a manual read:
1. Click the extension icon
2. Click "Read Card Now"

### Auto-filling Forms

The extension automatically fills forms on supported websites (currently PeakAccount):

1. Navigate to a supported form page (e.g., PeakAccount contact form)
2. Insert and read your ID card (or if already read, the data is cached)
3. The form will be automatically filled with:
   - Citizen ID (CID)
   - Thai name
   - English name
   - Address
   - Date of birth

You can disable auto-fill from the extension popup settings.

### Copying Data

From the extension popup, click the 📋 button next to any field to copy it to clipboard:
- Citizen ID
- Thai name
- English name
- Address

### Downloading Data

Click "Download JSON" in the extension popup to save card data as a JSON file for record keeping or integration with other applications.

## Settings

### Auto-fill Toggle

Enable or disable automatic form filling:
1. Click the extension icon
2. Toggle "Auto-fill forms" on/off

### Network Interface (Desktop App)

If you need to access the card reader from a different machine:

1. Open desktop app tray menu → "Extension Pairing & Settings..."
2. Select network interface:
   - **Localhost only (127.0.0.1)**: Most secure, extension must run on same computer
   - **All interfaces (0.0.0.0)**: Accessible from local network (less secure)
   - **Local Network (192.168.x.x)**: Accessible from specific local IP

3. Restart the server for changes to take effect
4. Update the extension's server URL if not using localhost

## Troubleshooting

### Extension Won't Connect

**Problem**: Status shows "Disconnected" or "Authentication Required"

**Solutions**:
1. Verify desktop application is running
2. Check server is started (tray icon tooltip should show "running")
3. Regenerate passcode in desktop app and update in extension
4. Check firewall isn't blocking port 8765

### Auto-fill Doesn't Work

**Problem**: Form fields aren't being filled automatically

**Solutions**:
1. Verify auto-fill is enabled in extension settings
2. Check that card data has been read (view in extension popup)
3. Some forms may use non-standard field names - the extension tries to detect common patterns
4. Manually copy/paste fields if auto-detection fails

### Invalid Passcode Error

**Problem**: "Invalid passcode" or "Authentication failed"

**Solutions**:
1. Generate a new passcode in desktop app
2. Copy the exact passcode (no extra spaces)
3. Paste into extension and click "Connect"
4. If issue persists, restart both desktop app and browser

### Card Not Detected

**Problem**: No card data appears after inserting card

**Solutions**:
1. Verify card reader is connected and recognized by desktop app
2. Try clicking "Read Card Now" in extension popup
3. Remove and re-insert card
4. Check desktop app logs for errors
5. Verify card is Thai National ID card (not other smart cards)

## Security & Privacy

- **Local Only**: All data processing happens on your computer
- **Passcode Protected**: Extension requires authentication to access card data
- **No Cloud Storage**: Card data is never sent to external servers
- **Secure Connection**: WebSocket connection is authenticated with passcode
- **Minimal Permissions**: Extension only requests necessary permissions

## Supported Websites

Currently supports auto-filling on:
- **PeakAccount** (secure.peakaccount.com) - Contact forms

More websites can be added by updating the `manifest.json` content_scripts section.

## Development

### Adding New Form Support

To add support for new websites:

1. Edit `manifest.json`:
   ```json
   "content_scripts": [{
     "matches": ["https://example.com/*"],
     "js": ["content-script.js"]
   }]
   ```

2. Update `content-script.js` field patterns if needed

3. Reload the extension in `chrome://extensions/`

### Customizing Field Mapping

Edit `FIELD_PATTERNS` in `content-script.js` to add detection patterns for your specific forms.

## API Documentation

The extension communicates with the desktop application via WebSocket API.

### WebSocket Endpoint

```
ws://localhost:8765/ws?passcode=YOUR_PASSCODE
```

### Message Types

**From Server**:
- `connected`: Connection established
- `card_inserted`: Card detected in reader
- `card_read`: Card data available
- `card_removed`: Card removed from reader
- `auth_required`: Authentication needed
- `auth_failed`: Invalid passcode

**From Client**:
- `ping`: Keep-alive heartbeat
- `read_card`: Trigger manual card read

### Card Data Format

```json
{
  "cid": "1234567890123",
  "thai_fullname": "นาย ทดสอบ ระบบ",
  "english_fullname": "Mr. Test System",
  "thai_name": {
    "prefix": "นาย",
    "first_name": "ทดสอบ",
    "last_name": "ระบบ"
  },
  "english_name": {
    "prefix": "Mr.",
    "first_name": "Test",
    "last_name": "System"
  },
  "date_of_birth": "1995-01-15",
  "address": "123 ถนนทดสอบ ...",
  "gender": "1",
  "issue_date": "2020-01-01",
  "expire_date": "2030-01-01"
}
```

## License

This project is part of the pythaiidcard library.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review desktop application logs
3. Open an issue on the GitHub repository

---

**Version**: 1.0.0
**Last Updated**: 2025-10-25
