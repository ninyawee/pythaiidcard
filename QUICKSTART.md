# Quick Start Guide

## For Users

### Installation

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install -y pcscd libpcsclite-dev python3-dev swig

# Install pythaiidcard
pip install pythaiidcard
```

### Basic Usage

```python
from pythaiidcard import ThaiIDCardReader

# Auto-connect and read card
reader = ThaiIDCardReader()
with reader.card_session():
    card = reader.read_card()
    print(f"Name: {card.english_fullname}")
    print(f"CID: {card.cid}")
```

### CLI Usage

```bash
# List readers
pythaiidcard list-readers

# Read card
pythaiidcard read

# Get help
pythaiidcard --help
```

## For Developers

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/ninyawee/pythaiidcard.git
cd pythaiidcard

# Install system dependencies
mise run install-deps

# Install Python dependencies
mise run dev

# View all available tasks
mise tasks
```

### Common Tasks

```bash
# Code quality
mise run lint         # Check linting
mise run format       # Format code
mise run verify       # Run all checks

# Documentation
mise run docs-serve   # Serve locally (http://localhost:8000)
mise run docs-build   # Build docs
mise run docs-deploy  # Deploy to GitHub Pages

# Build and publish
mise run build        # Build package
mise run publish-test # Test on TestPyPI
mise run publish      # Publish to PyPI
```

### Available Tasks

| Task | Description |
|------|-------------|
| `mise run build` | Build distribution packages |
| `mise run clean` | Clean build artifacts and cache |
| `mise run dev` | Install all dependencies |
| `mise run docs-build` | Build documentation |
| `mise run docs-deploy` | Deploy docs to GitHub Pages |
| `mise run docs-serve` | Serve docs locally |
| `mise run format` | Format code with ruff |
| `mise run format-check` | Check code formatting |
| `mise run install-deps` | Install system dependencies |
| `mise run lint` | Run linting checks |
| `mise run publish` | Publish to PyPI |
| `mise run publish-test` | Publish to TestPyPI |
| `mise run run` | Run pythaiidcard CLI |
| `mise run setup` | Setup project with uv |
| `mise run verify` | Run all verification checks |

## Documentation

- **Full Documentation**: https://ninyawee.github.io/pythaiidcard/ (when deployed)
- **Installation Guide**: [docs/installation.md](docs/installation.md)
- **Usage Guide**: [docs/usage.md](docs/usage.md)
- **API Reference**: [docs/api-reference.md](docs/api-reference.md)
- **Troubleshooting**: [docs/troubleshooting.md](docs/troubleshooting.md)
- **Publishing Guide**: [PUBLISHING.md](PUBLISHING.md)

## Recommended Hardware

**USB-C Smart Card Reader**
- Affiliate Link: https://s.shopee.co.th/9zpLTwW3c8
- Compatible with Thai National ID cards
- Works with any PC/SC compatible reader

## Support

- **Issues**: https://github.com/ninyawee/pythaiidcard/issues
- **Repository**: https://github.com/ninyawee/pythaiidcard

## License

ISC License - See [LICENSE](LICENSE) file for details.
