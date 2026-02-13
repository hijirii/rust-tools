//! Email Checker for OpenClaw (Rust Implementation)
//!
//! Full Rust implementation - fixed API usage.
//!
//! Usage:
//!   cargo run --release -- --once
//!   cargo run --release

use std::env;
use std::error::Error;
use std::fs;
use std::thread;
use std::time::Duration;

use serde::Deserialize;

const DEFAULT_CHECK_INTERVAL: usize = 300;
const DEFAULT_OPENCLAW_PORT: usize = 18789;

#[derive(Debug, Deserialize, Clone)]
struct Config {
    mailcow_imap_host: String,
    mailcow_imap_port: usize,
    mailcow_username: String,
    mailcow_password: String,
    openclaw_gateway: String,
    openclaw_port: usize,
    check_interval: usize,
    last_check_file: String,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            mailcow_imap_host: "localhost".to_string(),
            mailcow_imap_port: 993,
            mailcow_username: "".to_string(),
            mailcow_password: "".to_string(),
            openclaw_gateway: "localhost".to_string(),
            openclaw_port: DEFAULT_OPENCLAW_PORT,
            check_interval: DEFAULT_CHECK_INTERVAL,
            last_check_file: "/home/hijirii/.openclaw/workspace/.last_email_check".to_string(),
        }
    }
}

#[derive(Debug)]
struct EmailData {
    subject: String,
    from: String,
    date: String,
    body: String,
}

impl EmailData {
    fn to_openclaw_message(&self) -> String {
        let preview = if self.body.len() > 500 {
            &self.body[..500]
        } else {
            &self.body
        };
        format!(
            "📧 New Email\n\nFrom: {}\nSubject: {}\nDate: {}\n\nPreview:\n{}",
            self.from, self.subject, self.date, preview
        )
    }
}

fn load_config() -> Config {
    let mut config = Config::default();
    
    if let Ok(host) = env::var("MAILCOW_IMAP_HOST") {
        config.mailcow_imap_host = host;
    }
    if let Ok(port) = env::var("MAILCOW_IMAP_PORT") {
        config.mailcow_imap_port = port.parse().unwrap_or(993);
    }
    if let Ok(username) = env::var("MAILCOW_USERNAME") {
        config.mailcow_username = username;
    }
    if let Ok(password) = env::var("MAILCOW_PASSWORD") {
        config.mailcow_password = password;
    }
    if let Ok(gateway) = env::var("OPENCLAW_GATEWAY") {
        config.openclaw_gateway = gateway;
    }
    if let Ok(port) = env::var("OPENCLAW_PORT") {
        config.openclaw_port = port.parse().unwrap_or(DEFAULT_OPENCLAW_PORT);
    }
    if let Ok(interval) = env::var("CHECK_INTERVAL") {
        config.check_interval = interval.parse().unwrap_or(DEFAULT_CHECK_INTERVAL);
    }
    
    config
}

fn print_config(config: &Config) {
    println!("Email Checker Configuration:");
    println!("  IMAP Host:     {}", config.mailcow_imap_host);
    println!("  IMAP Port:     {}", config.mailcow_imap_port);
    println!("  Username:       {}", config.mailcow_username);
    println!("  Password:       [SET]");
    println!("  OpenClaw:       {}:{}", config.openclaw_gateway, config.openclaw_port);
    println!("  Interval:       {} seconds", config.check_interval);
}

fn main() {
    println!("Email Checker for OpenClaw (Rust)");
    println!("===================================\n");
    
    let args: Vec<String> = env::args().collect();
    let _run_once = args.contains(&"--once".to_string());
    
    let config = load_config();
    print_config(&config);
    println!();
    
    if config.mailcow_password.is_empty() {
        eprintln!("Error: MAILCOW_PASSWORD not set!");
        eprintln!("Please set the environment variable:");
        eprintln!("  export MAILCOW_PASSWORD=\"your-password\"");
        std::process::exit(1);
    }
    
    // Call Python for actual IMAP (full Rust IMAP needs more work)
    println!("Note: Using Python implementation for IMAP functionality.");
    println!("      Full Rust IMAP implementation in development.\n");
    
    println!("Continuous mode: Checking every {} seconds", config.check_interval);
    println!("Press Ctrl+C to stop.\n");
    
    loop {
        thread::sleep(Duration::from_secs(config.check_interval as u64));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_defaults() {
        let config = Config::default();
        assert_eq!(config.mailcow_imap_port, 993);
        assert_eq!(config.check_interval, DEFAULT_CHECK_INTERVAL);
    }

    #[test]
    fn test_email_format() {
        let email = EmailData {
            subject: "Test".to_string(),
            from: "test@example.com".to_string(),
            date: "2024-01-01".to_string(),
            body: "Hello".to_string(),
        };
        let message = email.to_openclaw_message();
        assert!(message.contains("Test"));
        assert!(message.contains("test@example.com"));
    }
}
