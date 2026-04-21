#!/usr/bin/env python3
"""Test the Gmail SMTP send flow.

Sends a test approval-workflow email containing the sales one-pager
(rendered from markdown to HTML) to the configured APPROVAL_EMAIL using
a Gmail App Password.
"""
import re
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import markdown
import tomllib

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / ".streamlit" / "secrets.toml"
SAMPLE = ROOT / "output" / "Whitepaper - True Enterprise Cost of Regulatory Fines" / "sales-one-pager.md"


def load_secrets() -> dict:
    if not SECRETS.exists():
        print(f"Secrets not found: {SECRETS}")
        print("Copy .streamlit/secrets.toml.example to .streamlit/secrets.toml and fill in values.")
        sys.exit(1)
    with open(SECRETS, "rb") as f:
        return tomllib.load(f)


def strip_yaml_frontmatter(text: str) -> str:
    if text.lstrip().startswith("---"):
        text = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.DOTALL)
    return text.strip()


def first_name(email: str) -> str:
    """Best-effort first-name extraction from an email address."""
    local = email.split("@", 1)[0]
    first = re.split(r"[._-]", local)[0]
    return first.capitalize() or "there"


def render_approval_email(
    *,
    recipient_email: str,
    asset_label: str,
    source_label: str,
    asset_md: str,
) -> tuple[str, str]:
    """Build the HTML and plain-text bodies for an approval-request email.

    Returns (html, plain).
    """
    name = first_name(recipient_email)
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p").lstrip("0").replace(" 0", " ")
    asset_html = markdown.markdown(asset_md, extensions=["tables", "fenced_code"])

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Symphony Approval Request</title>
</head>
<body style="margin:0;padding:0;background:#F4F4F7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#1F2937;line-height:1.55;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F4F4F7;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="640" cellpadding="0" cellspacing="0" border="0" style="max-width:640px;background:#FFFFFF;border-radius:16px;box-shadow:0 4px 24px rgba(15,23,42,0.06);overflow:hidden;">

          <!-- Header bar -->
          <tr>
            <td style="background:linear-gradient(135deg,#6366F1 0%,#8B5CF6 100%);padding:28px 36px;color:#FFFFFF;">
              <div style="font-size:11px;letter-spacing:2.4px;font-weight:600;text-transform:uppercase;opacity:0.85;">Project Symphony</div>
              <div style="font-size:22px;font-weight:700;margin-top:4px;">Approval Request</div>
              <div style="font-size:13px;opacity:0.85;margin-top:2px;">GTM Intelligence + Action Layer · PureFacts</div>
            </td>
          </tr>

          <!-- Greeting + context -->
          <tr>
            <td style="padding:32px 36px 8px 36px;">
              <p style="margin:0 0 14px 0;font-size:16px;">Hey {name},</p>
              <p style="margin:0 0 18px 0;font-size:15px;color:#374151;">
                Symphony just generated a new asset and it is waiting for your sign-off before it ships.
              </p>

              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 0 0;border-collapse:separate;border-spacing:0;">
                <tr>
                  <td style="padding:14px 18px;background:#F9FAFB;border:1px solid #E5E7EB;border-radius:10px;">
                    <div style="font-size:11px;letter-spacing:1.2px;color:#6B7280;text-transform:uppercase;font-weight:600;">Asset</div>
                    <div style="font-size:15px;font-weight:600;color:#111827;margin-top:2px;">{asset_label}</div>
                    <div style="font-size:12px;color:#6B7280;margin-top:8px;"><strong style="color:#374151;">Source:</strong> {source_label}</div>
                    <div style="font-size:12px;color:#6B7280;margin-top:2px;"><strong style="color:#374151;">Generated:</strong> {timestamp}</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Action callout -->
          <tr>
            <td style="padding:20px 36px 8px 36px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:separate;border-spacing:0;">
                <tr>
                  <td style="padding:18px 20px;background:#EEF2FF;border-left:4px solid #6366F1;border-radius:8px;">
                    <div style="font-size:13px;font-weight:700;color:#4338CA;letter-spacing:0.4px;text-transform:uppercase;margin-bottom:8px;">How to respond</div>
                    <div style="font-size:14px;color:#1F2937;margin-bottom:6px;">
                      <strong style="color:#059669;">Approve:</strong> Reply <strong>YES</strong> and Symphony ships it.
                    </div>
                    <div style="font-size:14px;color:#1F2937;">
                      <strong style="color:#B45309;">Request changes:</strong> Reply with your feedback and Symphony will revise.
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Asset content -->
          <tr>
            <td style="padding:24px 36px 8px 36px;">
              <div style="font-size:11px;letter-spacing:1.4px;color:#9CA3AF;text-transform:uppercase;font-weight:600;margin-bottom:6px;">Asset Preview</div>
              <div style="height:1px;background:#E5E7EB;margin-bottom:18px;"></div>
              <div style="font-size:15px;color:#1F2937;line-height:1.6;">
                {asset_html}
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 36px 32px 36px;">
              <div style="height:1px;background:#E5E7EB;margin-bottom:16px;"></div>
              <div style="font-size:12px;color:#9CA3AF;line-height:1.55;">
                Sent by <strong style="color:#6366F1;">Project Symphony</strong> · GTM Intelligence + Action Layer at PureFacts Financial Solutions.
                <br>This is an automated approval request. Reply YES to ship, or reply with feedback to revise.
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    plain = (
        f"Hey {name},\n\n"
        f"Symphony just generated a new asset and it is waiting for your sign-off before it ships.\n\n"
        f"Asset: {asset_label}\n"
        f"Source: {source_label}\n"
        f"Generated: {timestamp}\n\n"
        f"HOW TO RESPOND\n"
        f"  - Approve: reply YES and Symphony ships it.\n"
        f"  - Request changes: reply with your feedback and Symphony will revise.\n\n"
        f"--- ASSET PREVIEW ---\n\n"
        f"{asset_md}\n\n"
        f"---\n"
        f"Sent by Project Symphony, the GTM Intelligence + Action Layer at PureFacts.\n"
    )
    return html, plain


def send_email(secrets: dict, subject: str, html_body: str, plain_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Project Symphony <{secrets['GMAIL_ADDRESS']}>"
    msg["To"] = secrets["APPROVAL_EMAIL"]
    msg["Reply-To"] = secrets["APPROVAL_EMAIL"]
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(secrets["GMAIL_ADDRESS"], secrets["GMAIL_APP_PASSWORD"])
        smtp.send_message(msg)


def main() -> int:
    secrets = load_secrets()
    for key in ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "APPROVAL_EMAIL"):
        if not secrets.get(key) or "your-" in str(secrets.get(key, "")):
            print(f"Missing or placeholder secret: {key}")
            return 1

    if not SAMPLE.exists():
        print(f"Sample asset not found: {SAMPLE}")
        return 1

    md = strip_yaml_frontmatter(SAMPLE.read_text(encoding="utf-8"))
    asset_label = "Sales One-Pager"
    source_label = "True Enterprise Cost of Regulatory Fines (whitepaper)"
    subject = f"Symphony: approve {asset_label}?"

    html, plain = render_approval_email(
        recipient_email=secrets["APPROVAL_EMAIL"],
        asset_label=asset_label,
        source_label=source_label,
        asset_md=md,
    )

    print(f"Sending to {secrets['APPROVAL_EMAIL']} from {secrets['GMAIL_ADDRESS']}...")
    send_email(secrets, subject, html, plain)
    print("[OK] Email sent. Check the recipient inbox.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
