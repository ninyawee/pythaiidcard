# Web App Improvements (v2.3.0)

## Summary of Changes

This document outlines the improvements made to the web application in version 2.3.0 to fix display issues and improve user experience with event-driven reactivity.

## Changes Made

### 1. **Auto-Read Mode by Default** ✅

**Changed:** `auto_read_on_insert` default from `False` → `True`

**Location:** `api_server/services/card_monitor.py:34`

**Rationale:**
- Event-driven monitoring (v2.3.0) provides instant, reliable card detection
- No longer need to worry about hardware timing issues with polling-based approach
- Auto-read provides better UX - card data appears immediately on insertion

**Behavior:**
```python
# Before (v2.2.0)
card_monitor = CardMonitorService(connection_manager, auto_read_on_insert=False)

# After (v2.3.0)
card_monitor = CardMonitorService(connection_manager)  # auto_read_on_insert=True by default
```

### 2. **Removed Auto-Copy CID Checkbox** ✅

**Files Modified:**
- `web_app/index.html` - Removed checkbox HTML (lines 133-135)
- `web_app/app.js` - Removed auto-copy logic

**Before:**
```html
<label class="checkbox-label">
    <input type="checkbox" id="auto-copy" checked>
    <span>Auto-copy CID on read</span>
</label>
```

**After:** Removed completely

**Rationale:**
- Simplified UX - users can manually copy any field they need
- Avoided unexpected clipboard overwrites
- Copy buttons available for all fields including CID

### 3. **Fixed Field Name Mapping Issues** ✅

**Problem:** Web app was looking for incorrect field names from the API

**Root Cause:** Mismatch between API model field names and web app expectations

**API Model Fields (from `ThaiIDCard` model):**
```python
thai_name: Name          # Object with computed property
english_name: Name       # Object with computed property
issue_date: date         # Actual field name
expire_date: date        # Actual field name

# Computed properties:
thai_fullname: str       # thai_name.full_name
english_fullname: str    # english_name.full_name
```

**Web App Expected (WRONG - v2.2.0):**
```javascript
'name-th': 'name_th',           // ❌ Does not exist
'name-en': 'name_en',           // ❌ Does not exist
'issue-date': 'date_of_issue',  // ❌ Does not exist
'expire-date': 'date_of_expiry' // ❌ Does not exist
```

**Fixed Mapping (v2.3.0):**
```javascript
'name-th': 'thai_fullname',     // ✅ Computed field
'name-en': 'english_fullname',  // ✅ Computed field
'issue-date': 'issue_date',     // ✅ Actual field
'expire-date': 'expire_date'    // ✅ Actual field
```

**Files Modified:**
- `web_app/app.js:29-38` - Updated field mapping object
- `web_app/index.html:70,78,113,121` - Updated `data-field` attributes in copy buttons

### 4. **Auto-Clear on Card Removal** ✅

**Added:** Automatic card data clearing when card is removed

**Location:** `web_app/app.js:183-188`

**Implementation:**
```javascript
case 'card_removed':
    this.log('warning', 'Card removed');
    this.showToast('info', 'Card removed');
    // Auto-clear card data when card is removed
    this.clearCardData();
    break;
```

**Behavior:**
- When `card_removed` event is received from WebSocket
- Automatically clears the displayed card data
- Returns to welcome screen
- Prevents stale data from being displayed

**User Flow:**
1. Insert card → Data appears automatically
2. Remove card → Data clears automatically
3. Insert card again → Fresh data appears

## Field Name Reference

For future development, here's the complete field mapping reference:

### API Model (`ThaiIDCard.model_dump()`)

| Field Name | Type | Description | Computed? |
|------------|------|-------------|-----------|
| `cid` | `str` | Citizen ID (13 digits) | No |
| `thai_name` | `dict` | Thai name object | No |
| `english_name` | `dict` | English name object | No |
| `thai_fullname` | `str` | Full Thai name | ✅ Yes |
| `english_fullname` | `str` | Full English name | ✅ Yes |
| `date_of_birth` | `str` | Date of birth (ISO format) | No |
| `gender` | `str` | Gender code ("1"/"2") | No |
| `gender_text` | `str` | Gender text ("Male"/"Female") | ✅ Yes |
| `address` | `str` | Full address string | ✅ Yes |
| `address_info` | `dict` | Address object | No |
| `issue_date` | `str` | Card issue date (ISO format) | No |
| `expire_date` | `str` | Card expiry date (ISO format) | No |
| `card_issuer` | `str` | Issuing organization | No |
| `photo` | `bytes` | Raw photo bytes | No |
| `photo_base64` | `str` | Base64 encoded photo | Added by API |
| `age` | `int` | Current age | ✅ Yes |
| `is_expired` | `bool` | Expiry status | ✅ Yes |
| `days_until_expiry` | `int` | Days until expiry | ✅ Yes |

### Web App Display Mapping

| HTML Element ID | Field Name (API) | Copy Button `data-field` |
|----------------|------------------|--------------------------|
| `cid` | `cid` | `cid` |
| `name-th` | `thai_fullname` | `thai_fullname` |
| `name-en` | `english_fullname` | `english_fullname` |
| `dob` | `date_of_birth` | `date_of_birth` |
| `gender` | `gender_text` | `gender_text` |
| `address` | `address` | `address` |
| `issue-date` | `issue_date` | `issue_date` |
| `expire-date` | `expire_date` | `expire_date` |
| `photo` | `photo_base64` | N/A (image) |

## Testing the Changes

### 1. Start the API Server

```bash
uv run python -m api_server.main
```

Expected log:
```
INFO: Card monitoring started (version 2.3.0, event-driven mode)
INFO: Card monitor service initialized (version 2.3.0, auto-read: enabled)
```

### 2. Open Web App

Navigate to: http://localhost:8765/

### 3. Test Event Flow

#### Test 1: Card Insertion (Auto-Read)
1. **Insert card** into reader
2. **Expected behavior:**
   - Log: "Card detected in [reader name]"
   - Log: "Card detected - reading automatically..."
   - Toast: "Card detected - reading automatically..."
   - Data appears automatically within 2-5 seconds
   - All fields populated (Thai name, English name, issue date, expire date)

#### Test 2: Field Display
1. **Verify all fields** are populated:
   - ✅ Citizen ID (13 digits)
   - ✅ Name - Thai (full name in Thai)
   - ✅ Name - English (full name in English)
   - ✅ Date of Birth
   - ✅ Gender (Male/Female)
   - ✅ Address (full address)
   - ✅ Issue Date (card issue date)
   - ✅ Expire Date (card expiry date)
   - ✅ Photo (if available)

#### Test 3: Copy Functionality
1. **Click any copy button** (📋)
2. **Expected:** Field value copied to clipboard
3. **Expected:** Button shows checkmark (✓) for 2 seconds
4. **No auto-copy** of CID should occur

#### Test 4: Card Removal (Auto-Clear)
1. **Remove card** from reader
2. **Expected behavior:**
   - Log: "Card removed"
   - Toast: "Card removed"
   - Card data clears automatically
   - Welcome screen appears
   - No stale data remains

#### Test 5: Re-insertion
1. **Insert card again**
2. **Expected:** Fresh data read and displayed automatically
3. **No cache indicator** should appear (new read)

## Troubleshooting

### Issue: Thai/English names not showing

**Symptoms:** Empty fields for Name - Thai / Name - English

**Cause:** Web app using wrong field names (`name_th`, `name_en`)

**Solution:** ✅ Fixed in v2.3.0 - now uses `thai_fullname`, `english_fullname`

**Verify Fix:**
```javascript
// Open browser console on web app page
console.log(app.fields);
// Should show:
// { 'name-th': 'thai_fullname', 'name-en': 'english_fullname', ... }
```

### Issue: Issue/Expire dates not showing

**Symptoms:** Empty fields for Issue Date / Expire Date

**Cause:** Web app using wrong field names (`date_of_issue`, `date_of_expiry`)

**Solution:** ✅ Fixed in v2.3.0 - now uses `issue_date`, `expire_date`

**Verify Fix:**
```javascript
// Open browser console
console.log(app.fields);
// Should show:
// { 'issue-date': 'issue_date', 'expire-date': 'expire_date', ... }
```

### Issue: Data not auto-clearing on card removal

**Symptoms:** Old card data remains when card is removed

**Solution:** ✅ Fixed in v2.3.0 - auto-clear added to `card_removed` event handler

**Verify Fix:**
- Check browser console logs
- Should see: `clearCardData()` called when card removed
- Welcome screen should reappear

### Issue: Auto-read not working

**Symptoms:** Card detected but no automatic data read

**Cause:** `auto_read_on_insert` set to `False`

**Solution:** ✅ Fixed in v2.3.0 - default changed to `True`

**Verify:**
```bash
# Check server logs when card is inserted
# Should see:
INFO: Auto-read enabled - reading card data...
INFO: Card data read from hardware
```

## Backward Compatibility

All changes are **backward compatible** with existing integrations:

✅ WebSocket event format unchanged
✅ REST API endpoints unchanged
✅ Event types unchanged (`card_inserted`, `card_removed`, `card_read`)
✅ Field names in API responses unchanged

**Migration:** No changes required for API consumers. Simply update the web app files.

## Code Review Checklist

When reviewing or modifying the web app:

- [ ] Always use computed field names: `thai_fullname`, `english_fullname`
- [ ] Use actual field names: `issue_date`, `expire_date` (not `date_of_*`)
- [ ] Update both JavaScript field mapping AND HTML `data-field` attributes
- [ ] Test with actual card data, not mock data
- [ ] Verify auto-clear on `card_removed` event
- [ ] Ensure copy buttons use correct `data-field` values
- [ ] Check browser console for field mapping warnings

## Future Improvements

Potential enhancements for future versions:

1. **Expiry Warning Badge**: Show warning if card expires within 30 days
2. **Age Display**: Show computed age next to date of birth
3. **Address Parsing**: Display address components separately (district, province, etc.)
4. **Photo Placeholder Improvement**: Show card reader icon instead of camera
5. **Offline Mode**: Cache last read for offline viewing
6. **Export Function**: Download card data as JSON/PDF

---

**Version:** 2.3.0
**Date:** 2025-10-24
**Status:** ✅ Production Ready
