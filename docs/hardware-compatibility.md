# Hardware Compatibility

This page documents tested smartcard readers and their compatibility with pythaiidcard.

!!! info "Version Information"
    Last Updated: 2025-10-24
    API Server Version: 2.2.0

---

## Tested Card Readers

### Alcor Link AK9563 (Alcor Micro)

**Model:** Alcor Link AK9563 00 00
**Status:** ⚠️ Partially Compatible
**Recommended Mode:** On-demand (manual read only)

#### Capabilities

!!! success "Working Features"
    - ✅ Card detection (insertion/removal events)
    - ✅ Manual card reading (via REST API or WebSocket command)
    - ✅ Photo extraction (20-part JPEG, 5KB)
    - ✅ All data fields (CID, name, address, dates, etc.)
    - ✅ SHARED connection mode (SCARD_SHARE_SHARED)

!!! failure "Known Limitations"
    - ❌ Automatic read on card insertion
    - ❌ Multiple consecutive hardware reads without card removal

#### Hardware Limitations

##### Cannot Auto-Read on Insertion

**Symptom:** Card detection works, but automatic read fails with connection errors
**Error:** `Card was removed. (0x80100069)` immediately after insertion
**Cause:** Hardware/driver limitation - reader needs stabilization time after card insertion

!!! tip "Workaround"
    Disable auto-read and use on-demand mode (default in v2.2.0+). The system will detect card insertion and wait for manual read command.

##### Requires Card Removal Between Reads

**Symptom:** First read succeeds, subsequent reads fail or hang

!!! success "Solution"
    Version 2.1.0 implemented caching - serves cached data for repeated reads. Remove card to trigger fresh hardware read.

**User Workflow:**

1. Insert card
2. Click "Read Card" button (first read from hardware)
3. Data is cached for instant access
4. Remove card when done or when fresh read is needed

##### Connection Mode Requirements

!!! warning "Important"
    **Required:** SCARD_SHARE_SHARED mode (not EXCLUSIVE)
    **Reason:** EXCLUSIVE mode causes "card was reset" errors after first read
    **Fixed:** v2.0.0 changed default connection mode to SHARED

#### Configuration

##### Recommended Settings (Default)

```python
from api_server.services.card_monitor import CardMonitorService
from api_server.services.connection_manager import ConnectionManager

manager = ConnectionManager()
monitor = CardMonitorService(
    connection_manager=manager,
    auto_read_on_insert=False  # Default in v2.2.0+
)
```

##### Alternative (Not Recommended for AK9563)

```python
monitor = CardMonitorService(
    connection_manager=manager,
    auto_read_on_insert=True  # May fail with this reader
)
```

#### Usage Notes

**Best Practices:**

1. ✅ Use on-demand mode (default)
2. ✅ Detect card insertion events
3. ✅ Prompt user to trigger manual read via UI
4. ✅ Serve cached data for subsequent requests
5. ✅ Instruct user to remove card for fresh read

**Performance Results:**

| Operation | Time | Status |
|-----------|------|--------|
| Card insertion detection | < 1 second | ✅ Working |
| Manual read with photo | 2-3 seconds | ✅ Working |
| Cached read response | < 10ms | ✅ Working |
| Card removal detection | < 5 seconds | ✅ Working |
| Auto-read on insertion | N/A | ❌ Fails |

---

## General Hardware Requirements

### Minimum Requirements

- PC/SC compliant smart card reader
- Support for T=0 or T=1 protocol
- Compatible with Thai National ID card
  **ATR:** `3B 79 96 00 00 54 48 20 4E 49 44 20 31 37`

### System Dependencies (Linux)

```bash
# Required packages
sudo apt-get install pcscd libpcsclite-dev swig

# Start pcscd service
sudo systemctl start pcscd
sudo systemctl enable pcscd
```

See [Installation Guide](installation.md) for detailed setup instructions.

### Verification

#### Check Reader Detection

```bash
# List all connected readers
uv run python -c "from pythaiidcard import ThaiIDCardReader; print(ThaiIDCardReader.list_readers())"
```

#### Start API Server

```bash
# Start the desktop client server
uv run pythaiidcard-server

# Check server status
curl http://localhost:8765/api/status
```

Expected response:

```json
{
  "status": "running",
  "version": "2.2.0",
  "readers_available": 1,
  "card_detected": true,
  "reader_name": "Alcor Link AK9563 00 00"
}
```

---

## API Server Modes

### On-Demand Mode (Default - v2.2.0+)

**Behavior:**

1. Card inserted → `card_inserted` event broadcast
2. No automatic read attempt
3. User triggers manual read via button/API
4. First read fetches from hardware and caches
5. Subsequent reads serve cached data
6. Card removal invalidates cache

**Configuration:**

```python
CardMonitorService(manager, auto_read_on_insert=False)
```

**WebSocket Event:**

```json
{
  "type": "card_inserted",
  "message": "Card detected - ready for reading",
  "reader": "Alcor Link AK9563 00 00"
}
```

### Auto-Read Mode (Optional)

!!! warning "Compatibility"
    Auto-read mode may not work with all readers (e.g., Alcor Link AK9563). Use only with tested, compatible hardware.

**Behavior:**

1. Card inserted → Immediately reads from hardware
2. Photo data included automatically
3. Data cached for subsequent requests

**Configuration:**

```python
CardMonitorService(manager, auto_read_on_insert=True)
```

**WebSocket Event:**

```json
{
  "type": "card_inserted",
  "message": "Card detected - reading automatically...",
  "reader": "Reader Name"
}
```

---

## Reporting Hardware Issues

If you encounter issues with a specific card reader model, please help us improve compatibility by reporting:

### What to Include

1. **Reader Information**
    - Model name and manufacturer
    - ATR value from logs
    - Purchase link (if available)

2. **System Information**
    - Operating system and version
    - Python version
    - pythaiidcard version

3. **Error Details**
    - Specific error messages with timestamps
    - Test results with both auto-read and on-demand modes
    - Screenshots or log files

4. **Testing Results**
    - ✅ Card detection: Working/Not Working
    - ✅ Manual read: Working/Not Working
    - ✅ Photo extraction: Working/Not Working
    - ✅ Auto-read on insertion: Working/Not Working

### Where to Report

📝 **GitHub Issues:** [https://github.com/ninyawee/pythaiidcard/issues](https://github.com/ninyawee/pythaiidcard/issues)

!!! tip "Template"
    Use the "Hardware Compatibility Report" issue template for structured reporting.

---

## Future Hardware Testing

### Planned Testing

The following readers are planned for compatibility testing:

- [ ] ACS ACR122U
- [ ] SCM SCR331
- [ ] Identiv uTrust
- [ ] Gemalto readers
- [ ] HID OMNIKEY series

!!! question "Want to Help?"
    If you have access to any of these readers and a Thai National ID card, consider contributing test results!

### Contributions Welcome

We welcome community contributions for:

- ✅ Test results from different reader models
- ✅ Hardware-specific workarounds
- ✅ Driver compatibility notes
- ✅ Performance benchmarks
- ✅ Alternative connection modes

**How to Contribute:**

1. Fork the repository
2. Test with your hardware
3. Document results in `notes/HARDWARE_NOTES.md`
4. Submit a pull request

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.2.0 | 2025-10-24 | Documented Alcor Link AK9563 limitations, added on-demand mode as default |
| 2.1.0 | 2025-10-24 | Added caching strategy for readers with read limitations |
| 2.0.0 | 2025-10-24 | Fixed connection mode (EXCLUSIVE → SHARED) |

---

## Related Documentation

- [Installation Guide](installation.md) - System dependencies and setup
- [Usage Guide](usage.md) - Basic usage examples
- [API Reference](api-reference.md) - Complete API documentation
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
