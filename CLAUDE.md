# CLAUDE.md — Electrum YAI (Yottaflux)

## Project Overview

Electrum YAI is a lightweight Yottaflux (YAI) cryptocurrency wallet forked from Electrum-Ravencoin (which itself was forked from Electrum for Bitcoin). It is a Python 3.8+ desktop application supporting Qt GUI, text UI, and daemon modes. Key features include hardware wallet integration, Yottaflux asset management, and IPFS metadata resolution.

- **Version**: 1.2.2 (client), 4.4.6.0 (APK)
- **License**: MIT
- **Repository**: https://github.com/yottaflux/electrum-yai
- **Original**: Electrum by Thomas Voegtlin, Ravencoin conversion by kralverde, Yottaflux port

## Yottaflux Network Summary

- **Ticker**: YAI, smallest unit: corbie
- **PoW Algorithm**: X16RV2 (KawPOW disabled via far-future timestamp)
- **Mainnet P2PKH prefix**: 78 (addresses start with `Y`)
- **Mainnet P2SH prefix**: 137 (addresses start with `x`)
- **BIP44 coin type**: 5050 (mainnet), 1 (testnet)
- **Asset script marker**: `yai` (3 bytes after OP_YAI_ASSET 0xc0)
- **URI scheme**: `yottaflux:`
- **Genesis**: `000000f13b9584fc6830148c59ec77e5671a5ac3ff0f26a9ae0679c0ca40f579`

## Repository Structure

```
electrum-yai/
├── electrum/                  # Main Python package
│   ├── gui/                   # GUI implementations (qt/, text.py, stdio.py)
│   ├── plugins/               # Plugin system (trezor, ledger, keepkey, etc.)
│   ├── tests/                 # Unit and integration tests
│   ├── scripts/               # Utility scripts
│   ├── lnwire/                # Lightning Network wire protocol specs
│   ├── locale/                # i18n translation files
│   ├── wordlist/              # BIP39 wordlists
│   ├── _vendor/               # Vendored dependencies
│   ├── constants.py           # Network constants (YottafluxMainnet, YottafluxTestnet)
│   ├── version.py             # Version definitions
│   ├── wallet.py              # Wallet implementation
│   ├── transaction.py         # Transaction handling
│   ├── bitcoin.py             # Bitcoin/Yottaflux primitives
│   ├── asset.py               # Yottaflux asset operations
│   ├── ipfs_db.py             # IPFS metadata integration
│   ├── network.py             # Network communication
│   ├── daemon.py              # Daemon mode
│   ├── commands.py            # CLI commands
│   ├── bip21.py               # URI scheme (yottaflux:)
│   └── ...                    # ~75 additional modules
├── contrib/                   # Build scripts and requirements
│   ├── requirements/          # Pip requirement files
│   ├── build-linux/           # Linux build (AppImage, tarball)
│   ├── build-wine/            # Windows build via Wine
│   ├── osx/                   # macOS build
│   └── deterministic-build/   # Reproducible builds
├── run_electrum               # Main entry point script
├── setup.py                   # Package configuration
├── tox.ini                    # Test runner configuration
└── .cirrus.yml                # CI configuration
```

## Build & Development Setup

### Prerequisites

- Python >= 3.8
- `libsecp256k1-dev` (system package, required)
- `python3-pyqt5` (for GUI)

### Install for Development

```bash
# Install system dependencies (Debian/Ubuntu)
sudo apt-get install libsecp256k1-dev

# Install in development mode
python3 -m pip install --user -e .

# Install with extras
python3 -m pip install --user -e ".[tests]"       # for testing
python3 -m pip install --user -e ".[gui,crypto]"   # for GUI + fast crypto
python3 -m pip install --user -e ".[full]"          # everything except libsecp256k1
```

### Running

```bash
./run_electrum                    # Run from source
electrum_yai                      # Run if installed via pip
```

## Testing

### Run Tests

```bash
# Run all unit tests
pytest electrum/tests -v

# Run a specific test file
pytest electrum/tests/test_bitcoin.py -v

# Run with tox (includes coverage)
tox

# Run with coverage manually
coverage run --source=electrum \
    --omit='electrum/gui/*,electrum/plugins/*,electrum/scripts/*,electrum/tests/*' \
    -m pytest electrum/tests -v
coverage report
```

### Test Organization

- Tests are in `electrum/tests/`
- Base class: `ElectrumTestCase` (extends `unittest.IsolatedAsyncioTestCase`) in `electrum/tests/__init__.py`
- Supports async tests natively
- Use `@as_testnet` decorator to run individual tests in testnet mode
- Set `TESTNET = True` on test class to run entire class in testnet mode
- Regtest integration tests: `electrum/tests/regtest.py` (requires bitcoind + electrumx)

### CI

Cirrus CI runs on every push (`.cirrus.yml`):
1. **Flake8 linting** (mandatory, must pass before tests run)
2. **Unit tests** via tox on Python 3.8, 3.9, 3.10, 3.11
3. **Regtest functional tests** with bitcoind + electrumx
4. **Build artifacts**: Windows (Wine), Linux (AppImage, tarball), Android (APK)

## Linting

```bash
# Mandatory linters (must pass in CI)
flake8 . --count --select="E9,E101,E129,E273,E274,E703,E71,F63,F7,F82,W191,W29,B" \
    --ignore="B007,B009,B010,B019" --show-source --statistics \
    --exclude="*_pb2.py,electrum/_vendor/"
```

Mandatory lint rules include: syntax errors (E9), indentation (E101, W191), critical pyflakes (F63, F7, F82), and bugbear checks (B, excluding B007/B009/B010/B019).

## Code Conventions

### Style

- **4-space indentation** (no tabs) for Python and shell scripts
- **UTF-8** encoding, **LF** line endings
- Trim trailing whitespace
- Final newline in `.py` and `.sh` files
- See `.editorconfig` for full editor settings

### Architecture Patterns

- **Network switching**: `constants.net` is a module-level singleton (`YottafluxMainnet` or `YottafluxTestnet`). Import the `constants` module, not `net` directly.
- **Async**: Heavy use of `asyncio` throughout the networking and Lightning stack. The global event loop is managed via `electrum.util`.
- **Plugins**: Located in `electrum/plugins/`. Each plugin is a subdirectory with its own `__init__.py`. Hardware wallet plugins (trezor, ledger, keepkey, etc.) follow a common pattern.
- **GUI**: Qt GUI in `electrum/gui/qt/`. Text UI in `electrum/gui/text.py`.
- **Vendored deps**: In `electrum/_vendor/` — do not modify directly.
- **Protobuf**: Generated files end in `_pb2.py` — excluded from linting, do not edit.

### Yottaflux-Specific

- **Assets**: Asset logic in `electrum/asset.py`. Burn addresses/amounts defined in `electrum/constants.py` (`BurnAmounts`, `BurnAddresses` named tuples).
- **Asset script marker**: `b'yai'` — the 3-byte identifier after OP_YAI_ASSET (0xc0) in scripts.
- **Hashing algorithms**: Uses x16rv2 for PoW (KawPOW is disabled). C extensions: `x16r_hash`, `x16rv2_hash`, `kawpow` installed from git repos.
- **IPFS**: IPFS metadata resolution for assets in `electrum/ipfs_db.py`.
- **Network constants**: Mainnet uses address prefix 78 (P2PKH, starts with `Y`), BIP44 coin type 5050. Testnet uses prefix 111, coin type 1.
- **Message signing prefix**: `"\x19Yottaflux Signed Message:\n"`
- **Data directory**: `~/.electrum-yai` (Linux), `Electrum-YAI` (Windows/macOS)

### Dependencies

Core dependencies are in `contrib/requirements/requirements.txt`. Key packages:
- `aiorpcx` — async RPC
- `aiohttp` / `aiohttp_socks` — async HTTP with SOCKS proxy
- `qdarkstyle` — Qt dark theme
- `protobuf` — payment request protocol
- `x16r_hash`, `x16rv2_hash`, `kawpow` — PoW hash algorithms (from git)
- `ipfs-car-decoder`, `multiformats` — IPFS support

Hardware wallet deps: `contrib/requirements/requirements-hw.txt`

### Important Files

| File | Purpose |
|------|---------|
| `electrum/constants.py` | Network definitions, burn addresses, genesis blocks |
| `electrum/version.py` | Version constants |
| `electrum/commands.py` | All CLI/RPC commands |
| `electrum/wallet.py` | Core wallet logic |
| `electrum/transaction.py` | Transaction creation and parsing |
| `electrum/asset.py` | Yottaflux asset management |
| `electrum/bip21.py` | URI scheme (`yottaflux:`) |
| `electrum/simple_config.py` | Configuration system |
| `electrum/daemon.py` | Background daemon |
| `electrum/network.py` | Server connections |
| `run_electrum` | Entry point script |
| `setup.py` | Package metadata and install config |

## Common Tasks

### Adding a New Test

Create a test class inheriting from `ElectrumTestCase` in `electrum/tests/test_*.py`:

```python
from . import ElectrumTestCase

class TestMyFeature(ElectrumTestCase):
    def test_something(self):
        # synchronous test
        self.assertEqual(expected, actual)

    async def test_async_something(self):
        # async test (supported natively via IsolatedAsyncioTestCase)
        result = await some_async_function()
        self.assertEqual(expected, result)
```

### Modifying Network Constants

Edit `electrum/constants.py`. Both `YottafluxMainnet` and `YottafluxTestnet` must be kept in sync for any structural changes to `AbstractNet`.

### Working with Assets

Asset-related code is in `electrum/asset.py`. Burn addresses and amounts for asset operations (issue, reissue, sub-asset, unique, qualifier, restricted) are in `electrum/constants.py`.
