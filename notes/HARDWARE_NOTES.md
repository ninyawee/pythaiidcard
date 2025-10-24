# Hardware Compatibility Notes

**Last Updated:** 2025-10-24
**Version:** 2.2.0

---

## Tested Card Readers

### Alcor Link AK9563 (Alcor Micro)

**Model:** Alcor Link AK9563 00 00
**Status:** ⚠️ Partially Compatible
**Recommended Mode:** On-demand (manual read only)

#### Capabilities

✅ **Working:**
- Card detection (insertion/removal events)
- Manual card reading (via REST API or WebSocket command)
- Photo extraction (20-part JPEG, 5KB)
- All data fields (CID, name, address, dates, etc.)
- SHARED connection mode (SCARD_SHARE_SHARED)

❌ **Not Working:**
- Automatic read on card insertion
- Multiple consecutive hardware reads without card removal

#### Hardware Limitations

1. **Cannot Auto-Read on Insertion**
   - **Symptom:** Card detection works, but automatic read fails with connection errors
   - **Error:** `Card was removed. (0x80100069)` immediately after insertion
   - **Cause:** Hardware/driver limitation - reader needs stabilization time after card insertion
   - **Workaround:** Disable auto-read, use on-demand mode (default in v2.2.0+)

2. **Requires Card Removal Between Reads**
   - **Symptom:** First read succeeds, subsequent reads fail or hang
   - **Solution:** Implemented caching in v2.1.0 - serves cached data for repeated reads
   - **User Workflow:** Remove card to trigger fresh hardware read

3. **Connection Mode Requirements**
   - **Required:** SCARD_SHARE_SHARED mode (not EXCLUSIVE)
   - **Reason:** EXCLUSIVE mode causes "card was reset" errors after first read
   - **Fixed:** v2.0.0 changed default connection mode to SHARED

#### Configuration

**Recommended Settings:**
```python
CardMonitorService(
    connection_manager=manager,
    auto_read_on_insert=False  # Disable auto-read (default in v2.2.0)
)
```

**Alternative (Not Recommended for AK9563):**
```python
CardMonitorService(
    connection_manager=manager,
    auto_read_on_insert=True  # May fail with this reader
)
```

#### Usage Notes

**Best Practices:**
1. Use on-demand mode (default)
2. Detect card insertion events
3. Prompt user to trigger manual read via UI
4. Serve cached data for subsequent requests
5. Instruct user to remove card for fresh read

**Testing Results:**
- ✅ Card insertion detection: < 1 second
- ✅ Manual read with photo: 2-3 seconds
- ✅ Cached read response: < 10ms
- ✅ Card removal detection: < 5 seconds
- ❌ Auto-read on insertion: Fails with connection error

---

## General Hardware Requirements

### Minimum Requirements

- PC/SC compliant smart card reader
- Support for T=0 or T=1 protocol
- Compatible with Thai National ID card (ATR: `3B 79 96 00 00 54 48 20 4E 49 44 20 31 37`)

### System Dependencies (Linux)

```bash
# Required packages
sudo apt-get install pcscd libpcsclite-dev swig

# Start pcscd service
sudo systemctl start pcscd
sudo systemctl enable pcscd
```

### Verification

```bash
# Check if reader is detected
uv run python -c "from pythaiidcard import ThaiIDCardReader; print(ThaiIDCardReader.list_readers())"

# Start API server
uv run pythaiidcard-server

# Check server status
curl http://localhost:8765/api/status
```

---

## Reporting Hardware Issues

If you encounter issues with a specific card reader model:

1. Note the reader model and manufacturer
2. Capture the ATR value from logs
3. Document specific error messages
4. Test with both auto-read and on-demand modes
5. Report to: https://github.com/ninyawee/pythaiidcard/issues

Include:
- Reader model and manufacturer
- Operating system and version
- Error logs (with timestamps)
- ATR value
- Test results with different modes

---

## Future Hardware Support

**Planned Testing:**
- ACS ACR122U
- SCM SCR331
- Identiv uTrust
- Gemalto readers

**Contributions Welcome:**
- Test results from other reader models
- Hardware-specific workarounds
- Driver compatibility notes

---

**Version History:**
- v2.2.0 (2025-10-24): Documented Alcor Link AK9563 limitations, added on-demand mode
- v2.1.0 (2025-10-24): Added caching strategy for readers with read limitations
- v2.0.0 (2025-10-24): Fixed connection mode (EXCLUSIVE → SHARED)
