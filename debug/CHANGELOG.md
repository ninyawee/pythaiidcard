# Debug Interface Changelog

## 2025-10-23 - Version 2.0

### Added
- **New Compact Interface** (`app_compact.py`)
  - Modern dark gradient theme
  - Single-page layout with all controls in header
  - Inline control panel with reader selection
  - Color-coded status badges
  - Sleek card-based design with shadows and animations
  - Production-ready appearance
  - Quick launch script (`RUN_COMPACT.sh`)

### Fixed
- **System Check Issues**
  - Fixed false positive for missing Python dev headers
  - Added smart pyscard import check before system dependency validation
  - System check now verifies pyscard works instead of checking for system packages

- **Card Reader Connection**
  - Fixed applet selection response handling
  - Now accepts both `90 00` (success) and `61 XX` (success with more data) responses
  - Resolves "Failed to select Thai ID applet: 61 0A" error

- **Streamlit Warnings**
  - Fixed empty label accessibility warning in text_area
  - Replaced deprecated `use_container_width` with `width='stretch'`
  - Updated all buttons, images, and download buttons

### Changed
- Updated Python requirement from 3.14 to 3.13 for better compatibility
- Added `build-system` to pyproject.toml for editable package installation
- Improved documentation with interface comparison table

## 2025-10-23 - Version 1.0

### Initial Release
- Full-featured debug interface with tabs
- Reader scanning and connection management
- Card data reading with progress indicators
- Photo extraction (20 parts)
- Debug logging with timestamps
- Multiple export formats (JSON, CSV, Photo)
- System dependency checking
- Comprehensive error handling
