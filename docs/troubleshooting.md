# Troubleshooting

## Common Issues

### SystemDependencyError: Missing required system dependencies

**Problem:** When initializing `ThaiIDCardReader`, you get an error about missing system dependencies.

**Solution:** Install the required system packages:

=== "Ubuntu/Debian"
    ```bash
    sudo apt-get update
    sudo apt-get install -y pcscd libpcsclite-dev python3-dev swig
    ```

=== "Fedora/RHEL/CentOS"
    ```bash
    sudo dnf install -y pcsc-lite pcsc-lite-devel python3-devel swig
    ```

=== "Arch Linux"
    ```bash
    sudo pacman -S pcsclite swig python
    ```

**Workaround:** If dependencies are installed via other means:
```python
reader = ThaiIDCardReader(skip_system_check=True)
```

---

### NoReaderFoundError: No smart card reader found

**Problem:** The library cannot detect any smartcard readers.

**Symptoms:**
```
NoReaderFoundError: No smart card reader found. Please connect a reader.
```

**Solutions:**

1. **Check reader is connected:**
   ```bash
   lsusb  # Should show your USB smartcard reader
   ```

2. **Verify PC/SC daemon is running:**
   ```bash
   sudo systemctl status pcscd
   ```

   If not running:
   ```bash
   sudo systemctl start pcscd
   sudo systemctl enable pcscd  # Auto-start on boot
   ```

3. **Test reader detection:**
   ```bash
   pcsc_scan
   ```

   You should see your reader listed. Press `Ctrl+C` to exit.

4. **Check permissions:**
   ```bash
   sudo usermod -a -G scard $USER
   ```
   Then log out and log back in.

---

### NoCardDetectedError: No card detected

**Problem:** Reader is detected but no card is found.

**Symptoms:**
```
NoCardDetectedError: No card detected. Please insert a Thai ID card.
```

**Solutions:**

1. **Ensure card is properly inserted:**
   - Card should be fully inserted
   - Gold chip should be facing up and inserted first
   - Try removing and reinserting the card

2. **Verify card is detected:**
   ```bash
   pcsc_scan
   ```
   When you insert a card, you should see ATR information displayed.

3. **Check for card damage:**
   - Clean the chip with a soft cloth
   - Try a different card if available
   - Test the card in another reader

---

### InvalidCardError: Not a valid Thai ID card

**Problem:** A card is detected but it's not recognized as a Thai ID card.

**Symptoms:**
```
InvalidCardError: The card is not a valid Thai National ID card.
```

**Solutions:**

1. **Verify it's a Thai ID card:**
   - Should be a Thai National ID card issued by the Thai government
   - Older cards may not work (try a newer card)

2. **Check card type:**
   - Some cards may require different applet selection
   - Contact card issuer if the card should work but doesn't

---

### CardConnectionError: Failed to connect

**Problem:** Cannot establish connection to the card.

**Possible causes:**

1. **Card in use by another process:**
   ```bash
   # Kill any processes using the card
   sudo systemctl restart pcscd
   ```

2. **Reader malfunction:**
   - Disconnect and reconnect the reader
   - Try a different USB port
   - Test with a different reader

3. **Driver issues:**
   - Install proprietary drivers if needed
   - Check reader manufacturer website

---

### ImportError: No module named 'smartcard'

**Problem:** pyscard is not installed or failed to install.

**Symptoms:**
```
ImportError: No module named 'smartcard'
```

**Solutions:**

1. **Install system dependencies first:**
   ```bash
   sudo apt-get install pcscd libpcsclite-dev python3-dev swig
   ```

2. **Reinstall pyscard:**
   ```bash
   pip uninstall pyscard
   pip install pyscard --no-cache-dir
   ```

3. **If using uv:**
   ```bash
   uv sync --reinstall-package pyscard
   ```

---

### "No such file or directory: winscard.h"

**Problem:** Compilation error when installing pyscard.

**Solution:** Install libpcsclite-dev:
```bash
sudo apt-get install libpcsclite-dev
```

Then reinstall:
```bash
pip install pyscard --force-reinstall --no-cache-dir
```

---

### Permission denied when accessing reader

**Problem:** User doesn't have permission to access the smartcard reader.

**Symptoms:**
```
CardConnectionError: Permission denied
```

**Solutions:**

1. **Add user to scard group:**
   ```bash
   sudo usermod -a -G scard $USER
   ```
   Then log out and log back in.

2. **Check udev rules:**
   ```bash
   # List udev rules for PCSC
   ls -l /usr/lib/udev/rules.d/*pcsc*
   ```

3. **Run with sudo (temporary):**
   ```bash
   sudo python your_script.py
   ```
   ⚠️ Not recommended for production!

---

### Photo reading fails or is corrupted

**Problem:** Photo data is incomplete or invalid.

**Solutions:**

1. **Retry reading:**
   ```python
   reader = ThaiIDCardReader(retry_count=5)
   card = reader.read_card(include_photo=True)
   ```

2. **Clean card chip:**
   - Use a soft, dry cloth
   - Avoid using liquids

3. **Check card condition:**
   - Damaged cards may have corrupted photo data
   - Try a different card

4. **Verify photo data:**
   ```python
   if card.photo and len(card.photo) > 1000:
       card.save_photo()
   else:
       print("Photo data seems invalid")
   ```

---

### Slow performance

**Problem:** Reading cards takes too long.

**Solutions:**

1. **Skip photo reading if not needed:**
   ```python
   card = reader.read_card(include_photo=False)
   ```
   This reduces read time from ~3s to <1s.

2. **Use specific reader index:**
   ```python
   reader = ThaiIDCardReader(reader_index=0)
   ```
   Avoids auto-detection overhead.

3. **Reuse reader instance:**
   ```python
   reader = ThaiIDCardReader()
   reader.connect()

   # Read multiple cards
   for _ in range(10):
       card = reader.read_card()
       # Process card...

   reader.disconnect()
   ```

4. **Check USB connection:**
   - Use USB 2.0/3.0 ports (not USB hubs)
   - Avoid using extension cables

---

### TypeError: 'NoneType' object is not iterable

**Problem:** Trying to iterate over None value.

**Common cause:** Forgetting to check if photo exists:

```python
# Wrong
photo_path = card.save_photo()

# Correct
if card.photo:
    photo_path = card.save_photo()
else:
    print("No photo data")
```

---

### Encoding issues with Thai text

**Problem:** Thai characters display as garbage or question marks.

**Solutions:**

1. **Ensure UTF-8 encoding:**
   ```python
   # When writing to file
   with open("output.txt", "w", encoding="utf-8") as f:
       f.write(card.thai_fullname)
   ```

2. **Check terminal encoding:**
   ```bash
   export LANG=en_US.UTF-8
   export LC_ALL=en_US.UTF-8
   ```

3. **Use proper font:**
   - Ensure your terminal/editor supports Thai characters
   - Install Thai fonts if needed

---

### CID validation fails

**Problem:** CID appears valid but fails validation.

**Debugging:**
```python
from pythaiidcard import validate_cid, format_cid

cid = "1234567890123"
print(f"CID: {format_cid(cid)}")
print(f"Valid: {validate_cid(cid)}")

# Manual checksum calculation
digits = [int(d) for d in cid[:12]]
check_digit = int(cid[12])
checksum = sum((13-i) * d for i, d in enumerate(digits, 1)) % 11
expected = (11 - checksum) % 10
print(f"Expected: {expected}, Got: {check_digit}")
```

---

## Getting Help

If you're still experiencing issues:

1. **Check the logs:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Enable verbose mode (CLI):**
   ```bash
   pythaiidcard read --verbose
   ```

3. **Use the debug interface:**
   ```bash
   uv run streamlit run debug/app.py
   ```
   See real-time logs and connection status.

4. **Search existing issues:**
   - [GitHub Issues](https://github.com/ninyawee/pythaiidcard/issues)

5. **Create a new issue:**
   - Include Python version, OS, reader model
   - Provide error messages and logs
   - Describe steps to reproduce

---

## Platform-Specific Notes

### Ubuntu 22.04+
Works out of the box with standard installation.

### Ubuntu 20.04
May need to update pcscd:
```bash
sudo apt-get update
sudo apt-get upgrade pcscd
```

### Raspberry Pi
1. Install dependencies as usual
2. May need to add user to dialout group:
   ```bash
   sudo usermod -a -G dialout $USER
   ```

### WSL2 (Windows Subsystem for Linux)
USB passthrough required:
1. Install [usbipd-win](https://github.com/dorssel/usbipd-win)
2. Attach USB reader to WSL:
   ```powershell
   # In PowerShell (as Administrator)
   usbipd list
   usbipd bind --busid <BUSID>
   usbipd attach --wsl --busid <BUSID>
   ```

### Docker
USB device access required:
```dockerfile
# Add to Dockerfile
RUN apt-get update && apt-get install -y \
    pcscd libpcsclite-dev python3-dev swig

# Run with device access
docker run --device=/dev/bus/usb:/dev/bus/usb --privileged ...
```

---

## Compatibility

### Tested Readers
- Generic USB CCID readers
- Gemalto readers
- ACS ACR122U

### Known Issues
- Some older card readers may have compatibility issues
- Non-CCID readers may require additional drivers

### Card Compatibility
- Thai National ID cards issued after 2010 work well
- Older cards (pre-2010) may have issues
- New cards with updated chip work best
