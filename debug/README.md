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

Modern, sleek single-page interface with compact layout:

```bash
uv run streamlit run debug/app.py
```

The interface will open in your default browser at `http://localhost:8501`

### Interface Features

- **Design**: Modern dark theme with gradient cards
- **Layout**: Sidebar-based controls with clean main display area
- **Copy Buttons**: Quick copy for CID, names, and address
- **NHSO Data**: Read health insurance information
- **Laser ID**: Read laser-engraved ID from card
- **Performance**: Fast and responsive with minimal overhead

## Interface Overview

### Sidebar Controls

1. **🔍 Scan Readers**: Detect all available card readers
2. **📡 Available Readers**: List of detected readers with expandable details
   - Shows reader name, ATR, and card presence status
   - Connect button for each reader
3. **🔌 Connection Status**: Visual indicator of connection state
   - Green badge when connected
   - Disconnect button when active
4. **📖 Read Card**: Extract data section
   - Toggle photo inclusion
   - Read card data button
5. **📊 Additional Data**: Extra data operations
   - Read NHSO health insurance data
   - Read laser-engraved ID

### Main Display Area

- Displays all extracted information in formatted cards
- Shows card photo if available
- Quick copy buttons for CID, names, and address
- Export buttons for JSON, CSV, and photo data
- Card validity status and expiry warnings
- NHSO health insurance data display
- Laser ID display with copy functionality

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
