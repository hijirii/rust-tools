#!/usr/bin/env python3
"""
Email Checker Configuration
Copy this file to config.py and fill in your values
DO NOT commit config.py to GitHub!
"""

# Mailcow IMAP Configuration
MAILCOW_IMAP_HOST = '192.168.1.5'
MAILCOW_IMAP_PORT = 993
MAILCOW_USERNAME = 'hijirii@dtype.info'
MAILCOW_PASSWORD = None  # Set via environment variable for security

# SMTP Configuration (for replies)
SMTP_HOST = '192.168.1.5'
SMTP_PORT = 25

# OpenClaw Gateway Configuration
OPENCLAW_GATEWAY = 'localhost'
OPENCLAW_PORT = 18789

# Check Interval (seconds)
CHECK_INTERVAL = 300

# Last check file path
LAST_CHECK_FILE = '/home/hijirii/.openclaw/workspace/.last_email_check'
