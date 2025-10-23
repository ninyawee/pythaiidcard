# Quick Start - Thai ID Card Debug Interface

## Successfully Created!

The Streamlit debug interface for Thai ID card reader is now running.

## Access the Interface

Open your browser and navigate to:
- **Local**: http://localhost:8501
- **Network**: http://192.168.1.134:8501

## Current Status

✅ Streamlit app running
✅ Python 3.13 environment configured
✅ All dependencies installed (including pyarrow)
✅ Debug interface ready to use

## How to Use

1. **Scan Readers**: Click "🔍 Scan Readers" in the sidebar to detect your card reader
2. **Connect**: Select and connect to your Alcor Link AK9563 reader
3. **Read Card**: Insert your Thai ID card and click "📖 Read Card"
4. **View Data**: See all extracted information in the Card Data tab
5. **Export**: Download data as JSON, CSV, or save the photo

## Features Available

- Real-time reader detection
- Card connection status monitoring
- Progress tracking for photo extraction (20 parts)
- Live debug logs with timestamps
- Data validation (CID checksum, date conversion)
- Multiple export formats
- Photo display and download

## Stop the Server

To stop the Streamlit server, use:
```bash
# Find the process
ps aux | grep streamlit

# Or use ctrl+C if running in foreground
```

## Restart

```bash
uv run streamlit run debug/app.py --server.headless=true
```

## Notes

- Card reader: Alcor Link AK9563 00 00 detected
- Photo reading takes 10-20 seconds (20 parts @ 255 bytes each)
- Debug logs show APDU commands and responses
- Session state persists during browser refresh

Enjoy debugging your Thai ID card reader! 🪪
