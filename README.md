# Email Checker for OpenClaw

AI-powered email monitoring tool that checks IMAP and forwards emails to OpenClaw channels for automatic processing.

## Repository

https://github.com/hijirii/rust-tools

AI-powered email monitoring tool that checks IMAP and forwards emails to OpenClaw channels for automatic processing.

## Purpose

```
New Email → IMAP Check → OpenClaw Channel → AI Agent Reads & Processes
```

## Features

- IMAP email monitoring with SSL support
- Automatic forwarding to OpenClaw channels
- Configurable check intervals
- First-run detection (only new emails)
- Rate limiting and error handling

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MAILCOW_IMAP_HOST="your-mailcow-host"
export MAILCOW_IMAP_PORT="993"
export MAILCOW_USERNAME="your-email"
export MAILCOW_PASSWORD="your-password"
export OPENCLAW_GATEWAY="localhost"
export OPENCLAW_PORT="18789"

# Run once
python3 email_checker.py --once

# Run continuously
python3 email_checker.py
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

## Requirements

- Python 3.8+
- IMAP access to mailcow server

## License

MIT
