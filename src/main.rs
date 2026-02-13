// Email Checker for OpenClaw (Rust Implementation)
// 
// This is a Rust version of the email checker tool.
// For now, use the Python version: email_checker.py
//
// To build and run when Rust is installed:
//   cargo build --release
//   ./target/release/email_checker

use std::env;
use std::time::Duration;

mod imap;
mod openclaw;

fn main() {
    println!("Email Checker for OpenClaw (Rust)");
    println!("=================================");
    println!("Note: Python version (email_checker.py) is recommended for now.");
    println!();
    println!("Environment variables:");
    println!("  MAILCOW_IMAP_HOST");
    println!("  MAILCOW_IMAP_PORT");
    println!("  MAILCOW_USERNAME");
    println!("  MAILCOW_PASSWORD");
    println!("  OPENCLAW_GATEWAY");
    println!("  OPENCLAW_PORT");
    println!("  CHECK_INTERVAL");
    println!();
    println!("Usage:");
    println!("  python3 email_checker.py --once  # Run once");
    println!("  python3 email_checker.py          # Run continuously");
}
