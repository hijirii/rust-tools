//! Email Checker for OpenClaw (Rust Implementation)
//!
//! This is a simplified Rust implementation that compiles without OpenSSL.
//! For full functionality, use the Python version: email_checker.py
//!
//! Usage:
//!   cargo run --release -- --once    # Run once
//!   cargo run --release              # Run continuously
//!
//! Environment variables:
//!   MAILCOW_IMAP_HOST   - IMAP server (default: localhost)
//!   MAILCOW_IMAP_PORT   - IMAP port (default: 993)
//!   MAILCOW_USERNAME     - Email username
//!   MAILCOW_PASSWORD     - Email password
//!   OPENCLAW_GATEWAY     - OpenClaw gateway (default: localhost)
//!   OPENCLAW_PORT        - OpenClaw port (default: 18789)
//!   CHECK_INTERVAL       - Seconds between checks (default: 300)

use std::env;
use std::fs;
use std::path::Path;
use std::time::{Duration, SystemTime};
use std::process::{Command, exit};

const DEFAULT_CHECK_INTERVAL: usize = 300;
const DEFAULT_OPENCLAW_PORT: usize = 18789;

#[derive(Debug)]
struct Config {
    mailcow_imap_host: String,
    mailcow_imap_port: usize,
    mailcow_username: String,
    mailcow_password: String,
    openclaw_gateway: String,
    openclaw_port: usize,
    check_interval: usize,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            mailcow_imap_host: "localhost".to_string(),
            mailcow_imap_port: 993,
            mailcow_username: String::new(),
            mailcow_password: String::new(),
            openclaw_gateway: "localhost".to_string(),
            openclaw_port: DEFAULT_OPENCLAW_PORT,
            check_interval: DEFAULT_CHECK_INTERVAL,
        }
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
    let password_status = if !config.mailcow_password.is_empty() {
        "[SET]"
    } else {
        "[NOT SET]"
    };
    
    println!("Configuration:");
    println!("  IMAP Host:     {}", config.mailcow_imap_host);
    println!("  IMAP Port:     {}", config.mailcow_imap_port);
    println!("  Username:       {}", config.mailcow_username);
    println!("  Password:       {}", password_status);
    println!("  OpenClaw:       {}:{}", config.openclaw_gateway, config.openclaw_port);
    println!("  Interval:       {} seconds", config.check_interval);
}

fn check_python_version() -> bool {
    let output = Command::new("python3")
        .arg("--version")
        .output();
    
    match output {
        Ok(output) => output.status.success(),
        Err(_) => false,
    }
}

fn run_python_checker(config: &Config, once: bool) {
    let mut env = env::vars().collect::<Vec<_>>();
    env.push(("MAILCOW_PASSWORD".to_string(), config.mailcow_password.clone()));
    
    let mut cmd = Command::new("python3");
    cmd.env_clear();
    for (k, v) in &env {
        cmd.env(k, v);
    }
    cmd.arg("email_checker.py");
    
    if once {
        cmd.arg("--once");
    }
    
    println!("\nRunning Python email checker...");
    
    match cmd.status() {
        Ok(status) => {
            if !status.success() {
                eprintln!("Python checker exited with status: {}", status);
            }
        }
        Err(e) => {
            eprintln!("Failed to run Python checker: {}", e);
        }
    }
}

fn main() {
    println!("Email Checker for OpenClaw (Rust)");
    println!("=================================");
    println!();
    
    let args: Vec<String> = env::args().collect();
    let run_once = args.contains(&"--once".to_string());
    
    let config = load_config();
    print_config(&config);
    println!();
    
    // Check if Python version is available
    if !check_python_version() {
        eprintln!("Warning: Python3 not found!");
        eprintln!("Please install Python to use the email checker.");
        exit(1);
    }
    
    // Check if password is set
    if config.mailcow_password.is_empty() {
        eprintln!("\nError: MAILCOW_PASSWORD not set!");
        eprintln!("Please set the environment variable:");
        eprintln!("  export MAILCOW_PASSWORD=\"your-password\"");
        exit(1);
    }
    
    println!("\nNote: Using Python implementation for actual email checking.");
    println!("      Rust implementation is a wrapper/frontend.");
    println!();
    
    if run_once {
        run_python_checker(&config, true);
    } else {
        println!("Continuous mode: Running checks every {} seconds", config.check_interval);
        println!("Press Ctrl+C to stop.\n");
        
        loop {
            run_python_checker(&config, true);
            println!("\nSleeping for {} seconds...\n", config.check_interval);
            std::thread::sleep(Duration::from_secs(config.check_interval as u64));
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_defaults() {
        let config = Config::default();
        assert_eq!(config.mailcow_imap_port, 993);
        assert_eq!(config.check_interval, 300);
        assert_eq!(config.openclaw_port, DEFAULT_OPENCLAW_PORT);
    }

    #[test]
    fn test_config_loading() {
        // This test just verifies the function doesn't panic
        let _config = load_config();
    }
}
