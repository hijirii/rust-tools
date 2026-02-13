# Rust Tools for OpenClaw

**Repository**: https://github.com/hijirii/rust-tools

## Email Checker Tools

This repository provides email checking tools for the OpenClaw AI gateway system.

### Two Implementations

| Language | Status | Features |
|----------|--------|----------|
| **Python** | ✅ Production | Full IMAP, SMTP support |
| **Rust** | ✅ Compiles | Configuration, HTTP client |

### Python Version (Full Features)

```bash
pip install -r requirements.txt
export MAILCOW_PASSWORD="your-password"
python3 email_checker.py --once
```

### Rust Version

```bash
# Build
cargo build --release

# Run
MAILCOW_PASSWORD="your-password" ./target/release/email_checker
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MAILCOW_IMAP_HOST` | `localhost` | IMAP server |
| `MAILCOW_IMAP_PORT` | `993` | IMAP port |
| `MAILCOW_USERNAME` | - | Email username |
| `MAILCOW_PASSWORD` | - | Email password |
| `OPENCLAW_GATEWAY` | `localhost` | OpenClaw gateway |
| `OPENCLAW_PORT` | `18789` | OpenClaw port |
| `CHECK_INTERVAL` | `300` | Check interval (seconds) |

## Architecture

```
New Email → IMAP Check → OpenClaw Channel → AI Agent
```

## Dependencies

- ✅ Rust 1.93.1
- ✅ OpenSSL dev libraries
- ✅ cargo

## License

MIT
