# Email Checker for OpenClaw

**Repository**: https://github.com/hijirii/email-checker

Rust implementation of an IMAP monitor that forwards new emails to the OpenClaw Gateway for AI agent processing.

## Quick Start

```bash
# Build
cargo build --release

# Run
MAILCOW_PASSWORD="your-password" ./target/release/email-checker
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MAILCOW_IMAP_HOST` | `192.168.1.5` | Mailcow IMAP server |
| `MAILCOW_IMAP_PORT` | `993` | IMAP port |
| `MAILCOW_USERNAME` | `hijirii@dtype.info` | Email username |
| `MAILCOW_PASSWORD` | *(required)* | Email password |
| `OPENCLAW_GATEWAY` | `localhost` | OpenClaw gateway host |
| `OPENCLAW_PORT` | `18789` | OpenClaw gateway port |
| `OPENCLAW_HOOK_TOKEN` | *(default token)* | Webhook auth token |
| `CHECK_INTERVAL` | `300` | Check interval (seconds) |

## Architecture

```
Mailcow IMAP → Rust Checker → OpenClaw Gateway → Triage Agent → User Notification
```

## Systemd Service

```bash
systemctl --user enable email-checker
systemctl --user start email-checker
```

Service file: `/home/hijirii/.config/systemd/user/email-checker.service`

## Dependencies

- Rust 1.93+
- OpenSSL dev libraries (`libssl-dev`)
- Cargo

## License

MIT