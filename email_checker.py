#!/usr/bin/env python3
"""
Email Checker and Forwarder for OpenClaw
Checks mailcow IMAP and forwards new emails to OpenClaw channel for AI agent to process.

Purpose: AI agent (OpenClaw) can read and process emails automatically

Usage:
    python3 email_checker.py [--once]

Environment Variables:
    MAILCOW_IMAP_HOST: IMAP server (default: localhost)
    MAILCOW_IMAP_PORT: IMAP port (default: 993)
    MAILCOW_USERNAME: Email username
    MAILCOW_PASSWORD: Email password
    SMTP_HOST: SMTP server (for replies)
    SMTP_PORT: SMTP port
    OPENCLAW_GATEWAY: OpenClaw gateway (default: localhost)
    OPENCLAW_PORT: OpenClaw port (default: 18789)
    CHECK_INTERVAL: Seconds between checks (default: 300)
    LAST_CHECK_FILE: File to store last check time

Flow:
    New Email → IMAP Check → Send to OpenClaw Channel → AI Agent Reads & Processes
                                                                ↓
                                                        AI Decides: Reply/Ignore/Notify
"""

import os
import sys
import time
import json
import ssl
import imaplib
import email
from datetime import datetime
from typing import Optional, List, Dict
import urllib.request
import urllib.error

# Load configuration from config.py (not committed to GitHub)
try:
    from . import email_config as config
    MAILCOW_IMAP_HOST = getattr(config, 'MAILCOW_IMAP_HOST', '192.168.1.5')
    MAILCOW_IMAP_PORT = getattr(config, 'MAILCOW_IMAP_PORT', 993)
    MAILCOW_USERNAME = getattr(config, 'MAILCOW_USERNAME', 'hijirii@dtype.info')
    MAILCOW_PASSWORD = os.environ.get('MAILCOW_PASSWORD') or getattr(config, 'MAILCOW_PASSWORD', None)
    SMTP_HOST = getattr(config, 'SMTP_HOST', '192.168.1.5')
    SMTP_PORT = getattr(config, 'SMTP_PORT', 25)
    OPENCLAW_GATEWAY = getattr(config, 'OPENCLAW_GATEWAY', 'localhost')
    OPENCLAW_PORT = getattr(config, 'OPENCLAW_PORT', 18789)
    CHECK_INTERVAL = getattr(config, 'CHECK_INTERVAL', 300)
    LAST_CHECK_FILE = getattr(config, 'LAST_CHECK_FILE', '/home/hijirii/.openclaw/workspace/.last_email_check')
except ImportError:
    # Fallback to environment variables or defaults
    MAILCOW_IMAP_HOST = os.environ.get('MAILCOW_IMAP_HOST', '192.168.1.5')
    MAILCOW_IMAP_PORT = int(os.environ.get('MAILCOW_IMAP_PORT', '993'))
    MAILCOW_USERNAME = os.environ.get('MAILCOW_USERNAME', 'hijirii@dtype.info')
    MAILCOW_PASSWORD = os.environ.get('MAILCOW_PASSWORD')
    SMTP_HOST = os.environ.get('SMTP_HOST', '192.168.1.5')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '25'))
    OPENCLAW_GATEWAY = os.environ.get('OPENCLAW_GATEWAY', 'localhost')
    OPENCLAW_PORT = int(os.environ.get('OPENCLAW_PORT', '18789'))
    CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', '300'))
    LAST_CHECK_FILE = os.environ.get('LAST_CHECK_FILE', '/home/hijirii/.openclaw/workspace/.last_email_check')

# Verify required credentials
if not MAILCOW_PASSWORD:
    print("Warning: MAILCOW_PASSWORD not set. Set via environment variable or config.py")

class EmailChecker:
    def __init__(self):
        self.last_checked = self._load_last_checked()
    
    def _load_last_checked(self) -> Optional[datetime]:
        """Load last check time from file"""
        path = LAST_CHECK_FILE
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return datetime.fromisoformat(f.read().strip())
            except Exception as e:
                print(f"Warning: Could not load last check time: {e}")
        return None
    
    def _save_last_checked(self):
        """Save current time as last check time"""
        path = LAST_CHECK_FILE
        try:
            with open(path, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            print(f"Warning: Could not save last check time: {e}")
    
    def check_imap_emails(self) -> List[Dict]:
        """Check IMAP server for new emails"""
        host = MAILCOW_IMAP_HOST
        port = MAILCOW_IMAP_PORT
        username = MAILCOW_USERNAME
        password = MAILCOW_PASSWORD
        
        if not password:
            print("Error: MAILCOW_PASSWORD not set")
            return []
        
        emails = []
        
        try:
            # Connect to IMAP with SSL (handle self-signed certificates)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            mail = imaplib.IMAP4_SSL(host=host, port=port, ssl_context=context)
            
            # Login
            mail.login(username, password)
            
            # Select inbox
            mail.select('INBOX')
            
            # Search for unseen emails
            if self.last_checked:
                # Search by date
                date_str = self.last_checked.strftime("%d-%b-%Y")
                status, messages = mail.search(None, f'SINCE {date_str} UNSEEN')
            else:
                # First run - get all unseen
                status, messages = mail.search(None, 'UNSEEN')
            
            if status == 'OK' and messages[0]:
                for msg_id in messages[0].split():
                    # Fetch email
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status == 'OK' and msg_data:
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg_content = response_part[1]
                                email_msg = email.message_from_bytes(msg_content)
                                
                                # Parse email
                                subject = email_msg['subject'] or '(No Subject)'
                                from_addr = email_msg['from'] or '(Unknown)'
                                date_str = email_msg['date'] or datetime.now().isoformat()
                                
                                # Get body
                                body = self._get_email_body(email_msg)
                                
                                emails.append({
                                    'subject': subject,
                                    'from': from_addr,
                                    'date': date_str,
                                    'body': body[:500],  # Truncate for display
                                    'raw': msg_content,
                                })
            
            mail.logout()
            print(f"Found {len(emails)} new emails")
            
        except Exception as e:
            print(f"Error checking emails: {e}")
        
        return emails
    
    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extract email body text"""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_content()
                        break
                    except:
                        pass
        else:
            if msg.get_content_type() == "text/plain":
                try:
                    body = msg.get_content()
                except:
                    body = str(msg.get_payload())
        return body
    
    def forward_via_openclaw(self, email_data: Dict):
        """Forward email to OpenClaw channel for AI agent to process"""
        gateway = OPENCLAW_GATEWAY
        port = OPENCLAW_PORT
        
        # Send to OpenClaw channel - AI agent can read and process
        url = f"http://{gateway}:{port}/api/message"
        
        payload = {
            'channel': 'openclaw',  # Send to OpenClaw channel (AI can read)
            'message': f"📧 New Email Received\n\n"
                     f"From: {email_data['from']}\n"
                     f"Subject: {email_data['subject']}\n"
                     f"Date: {email_data['date']}\n\n"
                     f"Preview:\n{email_data['body'][:500]}...",
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                print(f"✓ Sent to OpenClaw channel: {email_data['subject']}")
        
        except urllib.error.URLError as e:
            print(f"✗ Failed to send to OpenClaw: {e}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def forward_via_smtp(self, email_data: Dict):
        """Forward email via local SMTP (mailcow) -备用方法"""
        host = SMTP_HOST
        port = SMTP_PORT
        # No longer sending to recipients - AI agent processes via OpenClaw channel
        print(f"📧 [SMTP备用] {email_data['subject']}")
    
    def run_once(self):
        """Check emails once and exit - for AI agent to process"""
        emails = self.check_imap_emails()
        
        for email_data in emails:
            if self.last_checked:
                # Only show new emails
                print(f"📧 New: {email_data['subject']} from {email_data['from']}")
                # Send to OpenClaw channel for AI agent
                self.forward_via_openclaw(email_data)
            else:
                # First run - just show
                print(f"📧 (First run) {email_data['subject']} from {email_data['from']}")
        
        self._save_last_checked()
    
    def run_forever(self):
        """Continuously check for new emails"""
        interval = CHECK_INTERVAL
        
        print(f"Email Checker Started - For AI Agent")
        print(f"====================================")
        print(f"IMAP: {MAILCOW_IMAP_HOST}:{MAILCOW_IMAP_PORT}")
        print(f"Sending to: OpenClaw channel (AI agent reads from here)")
        print(f"Check interval: {interval} seconds")
        print()
        
        if self.last_checked:
            print(f"Last check: {self.last_checked}")
        else:
            print("First run - will check all unseen emails")
        print()
        
        while True:
            try:
                emails = self.check_imap_emails()
                
                for email_data in emails:
                    print(f"📧 New: {email_data['subject']}")
                    # Send to OpenClaw channel for AI agent to read
                    self.forward_via_openclaw(email_data)
                    time.sleep(1)  # Rate limit
                
                self._save_last_checked()
                
            except KeyboardInterrupt:
                print("\nStopping...")
                break
            except Exception as e:
                print(f"Error: {e}")
            
            print(f"\nSleeping for {interval} seconds...")
            time.sleep(interval)


def main():
    # Check for --once flag
    run_once = '--once' in sys.argv
    
    checker = EmailChecker()
    
    if run_once:
        checker.run_once()
    else:
        checker.run_forever()


if __name__ == '__main__':
    main()
