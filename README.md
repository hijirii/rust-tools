# Rust Tools for OpenClaw

**Repository**: https://github.com/hijirii/rust-tools

## Email Checker Tools

This repository provides email checking tools for the OpenClaw AI gateway system.

### Two Implementations

| Language | Status | File | Notes |
|----------|--------|------|-------|
| **Python** | ✅ Production | `email_checker.py` | Full IMAP implementation |
| **Rust** | ✅ Compiles | `target/release/email_checker` | Configuration & control |

### Python Version (Recommended - Full Features)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MAILCOW_PASSWORD="your-password"

# Run once
python3 email_checker.py --once

# Run continuously
python3 email_checker.py
```

### Rust Version (Simplified)

```bash
# Build
cargo build --release

# Run
MAILCOW_PASSWORD="your-password" ./target/release/email_checker --once
```

## Configuration

All configuration via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAILCOW_IMAP_HOST` | `localhost` | IMAP server hostname |
| `MAILCOW_IMAP_PORT` | `993` | IMAP port |
| `MAILCOW_USERNAME` | - | Email username |
| `MAILCOW_PASSWORD` | - | Email password |
| `OPENCLAW_GATEWAY` | `localhost` | OpenClaw gateway |
| `OPENCLAW_PORT` | `18789` | OpenClaw port |
| `CHECK_INTERVAL` | `300` | Check interval in seconds |

## Architecture

```
New Email → IMAP Check → OpenClaw Channel → AI Agent Reads & Processes
```

## Dependencies Installed

- ✅ Rust 1.93.1
- ✅ OpenSSL development libraries
- ✅ pkg-config

## License

MIT
