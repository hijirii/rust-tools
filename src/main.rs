//! Email Checker for OpenClaw (Rust Implementation)
//!
//! IMAP monitor that forwards new emails to OpenClaw Gateway for AI agent processing.

use std::env;
use std::fs;
use std::thread;
use std::time::Duration;

use native_tls::TlsConnector;
use serde::Serialize;

const DEFAULT_CHECK_INTERVAL: u64 = 300;
const DEFAULT_OPENCLAW_PORT: u16 = 18789;
const MAX_EMAILS_PER_BATCH: usize = 50;

#[derive(Debug, Clone)]
struct Config {
    imap_host: String,
    imap_port: u16,
    username: String,
    password: String,
    gateway: String,
    gateway_port: u16,
    hook_token: String,
    check_interval: u64,
    last_uid_file: String,
}

impl Config {
    fn from_env() -> Self {
        let interval = env::var("CHECK_INTERVAL")
            .or_else(|_| env::var("CHECKINTERVAL"))
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(DEFAULT_CHECK_INTERVAL);

        Self {
            imap_host: env::var("MAILCOW_IMAP_HOST")
                .unwrap_or_else(|_| "192.168.1.5".to_string()),
            imap_port: env::var("MAILCOW_IMAP_PORT")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(993),
            username: env::var("MAILCOW_USERNAME")
                .unwrap_or_else(|_| "hijirii@dtype.info".to_string()),
            password: env::var("MAILCOW_PASSWORD")
                .expect("MAILCOW_PASSWORD must be set"),
            gateway: env::var("OPENCLAW_GATEWAY")
                .unwrap_or_else(|_| "localhost".to_string()),
            gateway_port: env::var("OPENCLAW_PORT")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(DEFAULT_OPENCLAW_PORT),
            hook_token: env::var("OPENCLAW_HOOK_TOKEN")
                .unwrap_or_else(|_| "email-checker-hook-secret-2026".to_string()),
            check_interval: if interval == 0 { DEFAULT_CHECK_INTERVAL } else { interval },
            last_uid_file: "/home/hijirii/.openclaw/workspace/.last_email_id".to_string(),
        }
    }
}

fn load_last_uid(path: &str) -> Option<u32> {
    fs::read_to_string(path).ok()?.trim().parse().ok()
}

fn save_last_uid(path: &str, uid: u32) {
    let _ = fs::write(path, uid.to_string());
}

fn parse_headers(raw: &[u8]) -> (String, String, String) {
    let text = String::from_utf8_lossy(raw);
    let mut from = String::from("(Unknown)");
    let mut subject = String::from("(No Subject)");
    let mut date = String::new();

    for line in text.lines() {
        let lower = line.to_lowercase();
        if lower.starts_with("from:") {
            from = line[5..].trim().to_string();
        } else if lower.starts_with("subject:") {
            subject = line[8..].trim().to_string();
        } else if lower.starts_with("date:") {
            date = line[5..].trim().to_string();
        }
        if line.is_empty() {
            break;
        }
    }
    (from, subject, date)
}

#[derive(Debug, Serialize)]
struct WebhookPayload {
    message: String,
    name: String,
    #[serde(rename = "agentId")]
    agent_id: String,
    #[serde(rename = "wakeMode")]
    wake_mode: String,
}

struct EmailInfo {
    from: String,
    subject: String,
    date: String,
    snippet: String,
}

fn send_webhook(config: &Config, emails: &[EmailInfo]) -> Result<(), Box<dyn std::error::Error>> {
    let url = format!(
        "http://{}:{}/hooks/agent",
        config.gateway, config.gateway_port
    );

    let mut lines = vec![format!(
        "📧 收到 {} 封新邮件，请你作为邮件分诊台 (Triage Agent) 对以下邮件进行分类，并使用 sessions_send 工具转发给对应负责的智能体（如果找不到归属则转发给 main）。不要直接回复我，而是要完成转发工作：\n",
        emails.len()
    )];
    for (i, em) in emails.iter().enumerate() {
        lines.push(format!("[{}] From: {}", i + 1, em.from));
        lines.push(format!("    Subject: {}", em.subject));
        lines.push(format!("    Date: {}", em.date));
        lines.push(format!("    Snippet: {}", em.snippet));
        lines.push(String::new());
    }

    let payload = WebhookPayload {
        message: lines.join("\n"),
        name: "Email Checker".to_string(),
        agent_id: "email".to_string(),
        wake_mode: "now".to_string(),
    };

    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(30))
        .build()?;
    let resp = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", config.hook_token))
        .json(&payload)
        .send()?;

    let body: serde_json::Value = resp.json()?;
    println!(
        "✓ Batch Agent dispatched ({} emails) -> runId: {}",
        emails.len(),
        body.get("runId").and_then(|v| v.as_str()).unwrap_or("unknown")
    );
    Ok(())
}

fn decode_body_text(bytes: &[u8]) -> String {
    // Try to decode as UTF-8, replacing invalid sequences
    String::from_utf8_lossy(bytes)
        .chars()
        .map(|c| if c == '\n' || c == '\r' { ' ' } else { c })
        .collect::<String>()
        .trim()
        .chars()
        .take(200)
        .collect()
}

fn check_emails(config: &Config) -> Result<bool, Box<dyn std::error::Error>> {
    println!(
        "Connecting to IMAP server {}:{}...",
        config.imap_host, config.imap_port
    );

    let tls = TlsConnector::builder()
        .danger_accept_invalid_certs(true)
        .build()?;
    let client = imap::connect(
        (config.imap_host.as_str(), config.imap_port),
        config.imap_host.as_str(),
        &tls,
    )?;

    let mut session = client
        .login(&config.username, &config.password)
        .map_err(|(e, _client)| e)?;

    session.select("INBOX")?;

    let last_uid = load_last_uid(&config.last_uid_file);

    // Search for all messages beyond last_uid (matches Python behavior)
    let search_query = match last_uid {
        Some(last) => format!("UID {}:*", last + 1),
        None => "ALL".to_string(),
    };

    let uids: Vec<u32> = {
        let mut result: Vec<u32> = session
            .uid_search(&search_query)?
            .into_iter()
            .collect();
        result.sort_unstable();
        result.truncate(MAX_EMAILS_PER_BATCH);
        result
    };

    if uids.is_empty() {
        println!("No new emails found.");
        session.logout()?;
        return Ok(false);
    }

    println!("Found {} new email(s).", uids.len());

    let mut emails: Vec<EmailInfo> = Vec::new();
    let mut max_uid: u32 = 0;

    for uid in &uids {
        if *uid > max_uid {
            max_uid = *uid;
        }

        let uid_str = uid.to_string();
        match session.uid_fetch(&uid_str, "(RFC822.HEADER BODY.PEEK[TEXT])") {
            Ok(messages) => {
                for msg in messages.iter() {
                    let (from, subject, date) = msg
                        .header()
                        .map(|h| parse_headers(h))
                        .unwrap_or_else(|| ("(Unknown)".to_string(), "(No Subject)".to_string(), String::new()));

                    let snippet = msg
                        .text()
                        .map(|t| decode_body_text(t))
                        .unwrap_or_else(|| "(empty)".to_string());

                    emails.push(EmailInfo { from, subject, date, snippet });
                }
            }
            Err(e) => {
                eprintln!("Failed to fetch email UID {}: {}", uid, e);
            }
        }
    }

    if !emails.is_empty() {
        match send_webhook(config, &emails) {
            Ok(_) => {}
            Err(e) => eprintln!("Failed to send webhook: {}", e),
        }

        if max_uid > 0 {
            save_last_uid(&config.last_uid_file, max_uid);
        }
    }

    session.logout()?;
    Ok(true)
}

fn main() {
    println!(
        r#"
╔═══════════════════════════════════════════════════════╗
║     Email Checker for OpenClaw (Rust v0.2.0)         ║
╚═══════════════════════════════════════════════════════╝"#
    );

    loop {
        let config = Config::from_env();

        println!("\nEmail Checker Configuration:");
        println!("   IMAP Host:     {}", config.imap_host);
        println!("   IMAP Port:     {}", config.imap_port);
        println!("   Username:      {}", config.username);
        println!("   Check Interval: {} seconds", config.check_interval);
        println!(
            "   OpenClaw:      {}:{}/hooks/agent",
            config.gateway, config.gateway_port
        );

        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");

        match check_emails(&config) {
            Ok(true) => println!(
                "[{}] Processed new emails. Waiting {}s before next check...",
                now, config.check_interval
            ),
            Ok(false) => println!(
                "[{}] No new emails. Waiting {}s before next check...",
                now, config.check_interval
            ),
            Err(e) => eprintln!(
                "[{}] Error checking emails: {}. Retrying in {}s...",
                now, e, config.check_interval
            ),
        }

        thread::sleep(Duration::from_secs(config.check_interval));
    }
}
