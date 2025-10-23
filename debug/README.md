# Thai ID Card Reader - Debug Interface

A Streamlit-based debug interface for testing and debugging the Thai ID card reader library.

## Features

- **Reader Detection**: Automatically scan and detect available PC/SC smart card readers
- **Live Connection**: Connect to readers and monitor card presence
- **Data Reading**: Read all data from Thai ID cards including:
  - Citizen ID (CID)
  - Personal information (Thai & English names)
  - Date of birth and age calculation
  - Gender
  - Address
  - Card issue and expiry dates
  - Photo (JPEG format)
- **Real-time Progress**: Visual progress indicators for photo reading
- **Debug Logging**: Comprehensive logging with timestamps
- **Data Export**: Export data in multiple formats (JSON, CSV, Photo)

## Installation

1. Install development dependencies:
```bash
uv sync --group dev
```

## Usage

### Compact Modern Interface (Recommended)

Modern, sleek single-page interface with compact layout:

```bash
uv run streamlit run debug/app_compact.py
```

### Full Debug Interface

Detailed interface with debug logs and multiple tabs:

```bash
uv run streamlit run debug/app.py
```

The interface will open in your default browser at `http://localhost:8501`

### Interface Comparison

| Feature | app_compact.py | app.py |
|---------|----------------|--------|
| **Design** | Modern, dark theme with gradient cards | Traditional Streamlit layout |
| **Layout** | Single-page compact | Multi-tab with sidebar |
| **Copy Buttons** | Quick copy for CID, names, address | No quick copy |
| **Debug Logs** | Minimal (console only) | Full debug log viewer |
| **Best For** | Quick card reading, production use | Debugging, development |
| **Performance** | Faster, less overhead | More features, more overhead |

## Interface Overview

### Sidebar Controls

1. **Scan Readers**: Detect all available card readers
2. **Reader List**: Shows detected readers with connection status
3. **Connect/Disconnect**: Manage reader connections
4. **Read Card**: Extract data from the inserted card
5. **Options**: Toggle photo reading on/off
6. **Clear Logs**: Reset debug logs

### Main Tabs

#### 📋 Card Data
- Displays all extracted information in a formatted view
- Shows card photo if available
- Export buttons for JSON, CSV, and photo data
- Card validity status and expiry warnings

#### 🐛 Debug Logs
- Real-time logging with timestamps
- Shows connection status, APDU commands, and errors
- Last 100 log entries displayed
- Helpful for troubleshooting reader issues

#### ℹ️ About
- Application information
- Usage instructions
- System information

## Troubleshooting

### No Readers Found
- Ensure your card reader is properly connected
- On Linux, check if `pcscd` service is running:
  ```bash
  sudo systemctl status pcscd
  ```
- Install required packages:
  ```bash
  sudo apt-get install pcscd libpcsclite-dev
  ```

### No Card Detected
- Verify the card is properly inserted
- Try removing and reinserting the card
- Check if the card is a Thai National ID card

### Connection Errors
- Restart the pcscd service:
  ```bash
  sudo systemctl restart pcscd
  ```
- Check reader permissions
- Try disconnecting and reconnecting the reader

### Photo Reading Issues
- Photo reading can take 10-20 seconds
- Watch the progress indicator
- Uncheck "Include Photo" if you only need text data

## Development

The debug interface uses:
- **Streamlit**: Web UI framework
- **pythaiidcard**: Core library for card reading
- **Pydantic**: Data validation and models
- **PIL/Pillow**: Image handling

## Features Demonstrated

This debug interface showcases all features of the `pythaiidcard` library:

- Reader scanning and selection
- Connection management
- Data reading with error handling
- Progress callbacks for long operations
- Photo extraction and display
- Data validation and parsing
- Export capabilities

## Tips

- Use the debug logs to understand the APDU command flow
- Export data for testing without physical card access
- Monitor card expiry dates for validation testing
- Test different reader types and configurations
