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
import sys
import os as _os
_config_path = _os.path.dirname(_os.path.abspath(__file__))
if _config_path not in sys.path:
    sys.path.insert(0, _config_path)

# Load configuration from email_config.py (not committed to GitHub)
try:
    import email_config as config
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
    OPENCLAW_HOOK_TOKEN = os.environ.get('OPENCLAW_HOOK_TOKEN', 'email-checker-hook-secret-2026')
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
    OPENCLAW_HOOK_TOKEN = os.environ.get('OPENCLAW_HOOK_TOKEN', 'email-checker-hook-secret-2026')

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
    
    def _get_last_email_id(self) -> Optional[int]:
        """Load last processed email ID from file"""
        path = LAST_CHECK_FILE.replace('last_email_check', 'last_email_id')
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return int(f.read().strip())
            except Exception as e:
                print(f"Warning: Could not load last email ID: {e}")
        return None
    
    def _save_last_email_id(self, email_id: int):
        """Save last processed email ID"""
        path = LAST_CHECK_FILE.replace('last_email_check', 'last_email_id')
        try:
            with open(path, 'w') as f:
                f.write(str(email_id))
        except Exception as e:
            print(f"Warning: Could not save last email ID: {e}")
    
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
            
            # Search for emails since last check (use date, not UNSEEN flag)
            # UNSEEN gets cleared after checking, so use date-based search instead
            last_email_id = self._get_last_email_id()
            
            if last_email_id:
                # Get emails with ID greater than last processed
                status, all_messages = mail.search(None, 'ALL')
                if status == 'OK' and all_messages[0]:
                    msg_ids = [int(x) for x in all_messages[0].split() if int(x) > last_email_id]
                    messages = (b' '.join(str(x).encode() for x in msg_ids),)
                else:
                    messages = (b'',)
            else:
                # First run - get all recent emails (past 7 days)
                from datetime import timedelta
                week_ago = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
                status, messages = mail.search(None, f'SINCE {week_ago}')
            
            if status == 'OK' and messages[0]:
                for msg_id_bytes in messages[0].split():
                    msg_id = int(msg_id_bytes)
                    # Fetch email
                    status, msg_data = mail.fetch(str(msg_id), '(RFC822)')
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
                                    'id': msg_id,
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
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
        else:
            if msg.get_content_type() == "text/plain":
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    body = str(msg.get_payload())
        return body
    
    def notify_batch_webhook(self, emails: List[Dict]):
        """Notify OpenClaw via agent hook with a batch of emails"""
        if not emails:
            return
            
        gateway = OPENCLAW_GATEWAY
        port = OPENCLAW_PORT
        token = OPENCLAW_HOOK_TOKEN
        
        url = f"http://{gateway}:{port}/hooks/agent"
        
        lines = [f"📧 收到 {len(emails)} 封新邮件，请你作为邮件分诊台 (Triage Agent) 对以下邮件进行分类，并使用 sessions_send 工具转发给对应负责的智能体 （如果找不到归属则转发给 main）。不要直接回复我，而是要完成转发工作：\n"]
        for i, em in enumerate(emails, 1):
            lines.append(f"[{i}] From: {em['from']}")
            lines.append(f"    Subject: {em['subject']}")
            lines.append(f"    Date: {em['date']}")
            lines.append(f"    Snippet: {em['body'][:200].replace(chr(10), ' ')}")
            lines.append("")
            
        payload = {
            'message': "\n".join(lines),
            'name': 'Email Checker',
            'agentId': 'email',
            'wakeMode': 'now'
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            req.add_header('Authorization', f'Bearer {token}')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                print(f"✓ Batch Agent dispatched ({len(emails)} emails) -> runId: {result.get('runId', 'unknown')}")
        
        except urllib.error.URLError as e:
            print(f"✗ Webhook failed: {e}")
        except Exception as e:
            print(f"✗ Webhook error: {e}")

    def run_once(self):
        """Check emails once and exit - for AI agent to process"""
        emails = self.check_imap_emails()
        
        if emails:
            print(f"📧 Found {len(emails)} new emails, sending batch notification...")
            self.notify_batch_webhook(emails)
            
            # Save last email ID to avoid duplicates
            max_id = max(em['id'] for em in emails)
            self._save_last_email_id(max_id)
            print(f"✓ Saved last email ID: {max_id}")
        
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
                
                if emails:
                    print(f"📧 Found {len(emails)} new emails, sending batch notification...")
                    self.notify_batch_webhook(emails)
                    
                    # Save last email ID to avoid duplicates
                    max_id = max(em['id'] for em in emails)
                    self._save_last_email_id(max_id)
                    print(f"✓ Saved last email ID: {max_id}")
                
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
    # Handle --reply option
    if '--reply' in sys.argv:
        import argparse
        parser = argparse.ArgumentParser(description='Send email reply')
        parser.add_argument('--reply', dest='email_id', nargs='?', const='fake', help='Email ID to reply to')
        parser.add_argument('--to', dest='to_addr', required=True, help='Recipient email address')
        parser.add_argument('--subject', dest='subject', required=True, help='Email subject')
        parser.add_argument('--body', dest='body', required=True, help='Email body')
        parser.add_argument('--in-reply-to', dest='in_reply_to', help='In-Reply-To header')
        parser.add_argument('--references', dest='references', help='References header')
        args = parser.parse_args()
        
        # Send via a separate function or use existing one
        # For simplicity, we just reuse the send_reply_via_smtp logic
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.header import Header
        
        host = SMTP_HOST
        port = SMTP_PORT
        username = MAILCOW_USERNAME
        password = MAILCOW_PASSWORD
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = args.to_addr
        msg['Subject'] = Header(args.subject, 'utf-8')
        
        if args.in_reply_to:
            msg['In-Reply-To'] = args.in_reply_to
        if args.references:
            msg['References'] = args.references
        
        msg.attach(MIMEText(args.body, 'plain', 'utf-8'))
        
        try:
            if port == 465:
                with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as server:
                    server.login(username, password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(host, port, timeout=30) as server:
                    server.starttls(context=context)
                    server.login(username, password)
                    server.send_message(msg)
            print(f"✓ Reply sent to {args.to_addr}")
            sys.exit(0)
        except Exception as e:
            print(f"✗ Failed to send reply: {e}")
            sys.exit(1)
            
    main()
