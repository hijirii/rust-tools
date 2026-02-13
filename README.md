# Rust Tools for OpenClaw

**Repository**: https://github.com/hijirii/rust-tools

## Email Checker Tools

This repository provides email checking tools for the OpenClaw AI gateway system.

### Two Implementations

| Language | Status | File | Notes |
|----------|--------|------|-------|
| **Python** | ✅ Ready | `email_checker.py` | Production ready, works now |
| **Rust** | 📦 Source | `src/main.rs` | Requires Rust installation |

### Python Version (Recommended)

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

### Rust Version (In Development)

```bash
# Install Rust first (if not installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build
cargo build --release

# Run
./target/release/email_checker
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

## License

MIT
