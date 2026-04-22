"""Reusable Gmail SMTP sender for Symphony approval emails."""
from __future__ import annotations

import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import markdown

from lib.textutils import strip_yaml_frontmatter


def _first_name(email: str) -> str:
    local = email.split("@", 1)[0]
    first = re.split(r"[._-]", local)[0]
    return first.capitalize() or "there"


# Local alias kept so the existing call site reads naturally. The single
# canonical implementation now lives in lib.textutils -- both this file and
# lib.distribution import the same function, so they can never drift apart.
_strip_yaml = strip_yaml_frontmatter


def render_approval_email(
    *,
    recipient_email: str,
    asset_label: str,
    source_label: str,
    asset_md: str,
    approve_url: str | None = None,
) -> tuple[str, str]:
    """Build (html, plain) for a Symphony approval email.

    If approve_url is provided, the email shows a primary button linking to that URL.
    Otherwise the email instructs the user to reply YES.
    """
    name = _first_name(recipient_email)
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p").lstrip("0").replace(" 0", " ")
    body_md = _strip_yaml(asset_md)
    asset_html = markdown.markdown(body_md, extensions=["tables", "fenced_code"])

    if approve_url:
        action_block = f"""
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 0 0;">
          <tr>
            <td align="center">
              <a href="{approve_url}" target="_blank" style="display:inline-block;background:linear-gradient(135deg,#818CF8 0%,#A78BFA 50%,#E879F9 100%);color:#FFFFFF;text-decoration:none;font-weight:700;padding:14px 28px;border-radius:12px;font-size:15px;letter-spacing:0.3px;box-shadow:0 4px 16px rgba(129,140,248,0.40);">Approve and Execute</a>
            </td>
          </tr>
        </table>
        <p style="text-align:center;font-size:12px;color:#9CA3AF;margin-top:12px;">Or reply with your feedback to revise the brief.</p>
        """
    else:
        action_block = """
        <div style="font-size:14px;color:#1F2937;margin-bottom:6px;">
          <strong style="color:#059669;">Approve:</strong> Reply <strong>YES</strong> and Symphony ships it.
        </div>
        <div style="font-size:14px;color:#1F2937;">
          <strong style="color:#B45309;">Request changes:</strong> Reply with your feedback and Symphony will revise.
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Symphony Approval Request</title>
  <style>
    /* Gmail respects <style> in <head>. Some clients strip it -- that's fine,
       the email still renders, just with default heading sizes in the body
       preview. The inline styles on every other element guarantee the chrome
       (header, action box, footer) always renders correctly. */
    .symphony-brief h1, .symphony-brief h2, .symphony-brief h3,
    .symphony-brief h4, .symphony-brief h5, .symphony-brief h6 {{
      color: #111827;
      font-weight: 700;
      line-height: 1.25;
      margin: 18px 0 8px 0;
    }}
    .symphony-brief h1 {{ font-size: 22px; }}
    .symphony-brief h2 {{ font-size: 18px; }}
    .symphony-brief h3 {{ font-size: 16px; }}
    .symphony-brief h4, .symphony-brief h5, .symphony-brief h6 {{ font-size: 15px; }}
    .symphony-brief p {{ margin: 8px 0; }}
    .symphony-brief ul, .symphony-brief ol {{ margin: 8px 0 8px 22px; padding: 0; }}
    .symphony-brief li {{ margin: 4px 0; }}
    .symphony-brief code {{
      background: #F3F4F6; padding: 1px 6px; border-radius: 4px;
      font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 13px;
    }}
    .symphony-brief table {{ border-collapse: collapse; margin: 12px 0; width: 100%; }}
    .symphony-brief th, .symphony-brief td {{
      border: 1px solid #E5E7EB; padding: 6px 10px; text-align: left; font-size: 14px;
    }}
    .symphony-brief th {{ background: #F9FAFB; font-weight: 600; }}

    /* Mobile responsiveness: collapse the 640px wrapper to fluid width on
       phones, tighten header padding, shrink the title slightly. Without this
       the email scrolls horizontally on most phone email clients. */
    @media only screen and (max-width: 600px) {{
      .symphony-shell {{ width: 100% !important; max-width: 100% !important; border-radius: 0 !important; }}
      .symphony-pad {{ padding-left: 20px !important; padding-right: 20px !important; }}
      .symphony-title {{ font-size: 18px !important; }}
      .symphony-brief h1 {{ font-size: 19px; }}
      .symphony-brief h2 {{ font-size: 17px; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background:#F4F4F7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#1F2937;line-height:1.55;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F4F4F7;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" class="symphony-shell" width="640" cellpadding="0" cellspacing="0" border="0" style="max-width:640px;background:#FFFFFF;border-radius:16px;box-shadow:0 4px 24px rgba(15,23,42,0.06);overflow:hidden;">

          <tr>
            <td class="symphony-pad" style="background:linear-gradient(135deg,#818CF8 0%,#A78BFA 50%,#E879F9 100%);padding:28px 36px;color:#FFFFFF;">
              <div style="font-size:11px;letter-spacing:2.4px;font-weight:600;text-transform:uppercase;opacity:0.85;">Project Symphony</div>
              <div class="symphony-title" style="font-size:22px;font-weight:700;margin-top:4px;">Approval Request</div>
              <div style="font-size:13px;opacity:0.85;margin-top:2px;">GTM Intelligence + Action Layer · PureFacts</div>
            </td>
          </tr>

          <tr>
            <td class="symphony-pad" style="padding:32px 36px 8px 36px;">
              <p style="margin:0 0 14px 0;font-size:16px;">Hey {name},</p>
              <p style="margin:0 0 18px 0;font-size:15px;color:#374151;">
                Symphony just produced a strategic brief and is waiting for your sign-off before executing the campaign.
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

          <tr>
            <td class="symphony-pad" style="padding:20px 36px 8px 36px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:separate;border-spacing:0;">
                <tr>
                  <td style="padding:18px 20px;background:#EEF2FF;border-left:4px solid #818CF8;border-radius:8px;">
                    <div style="font-size:13px;font-weight:700;color:#4338CA;letter-spacing:0.4px;text-transform:uppercase;margin-bottom:12px;">How to respond</div>
                    {action_block}
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td class="symphony-pad" style="padding:24px 36px 8px 36px;">
              <div style="font-size:11px;letter-spacing:1.4px;color:#9CA3AF;text-transform:uppercase;font-weight:600;margin-bottom:6px;">Brief Preview</div>
              <div style="height:1px;background:#E5E7EB;margin-bottom:18px;"></div>
              <div class="symphony-brief" style="font-size:15px;color:#1F2937;line-height:1.6;">
                {asset_html}
              </div>
            </td>
          </tr>

          <tr>
            <td class="symphony-pad" style="padding:24px 36px 32px 36px;">
              <div style="height:1px;background:#E5E7EB;margin-bottom:16px;"></div>
              <div style="font-size:12px;color:#9CA3AF;line-height:1.55;">
                Sent by <strong style="color:#818CF8;">Project Symphony</strong> · GTM Intelligence + Action Layer at PureFacts Financial Solutions.
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    plain_action = (
        f"APPROVE AND EXECUTE: {approve_url}\n\nOr reply with feedback to revise the brief.\n"
        if approve_url
        else "Reply YES to approve, or reply with feedback to revise.\n"
    )

    plain = (
        f"Hey {name},\n\n"
        f"Symphony just produced a strategic brief and is waiting for your sign-off before executing the campaign.\n\n"
        f"Asset: {asset_label}\n"
        f"Source: {source_label}\n"
        f"Generated: {timestamp}\n\n"
        f"HOW TO RESPOND\n"
        f"{plain_action}\n"
        f"--- BRIEF PREVIEW ---\n\n"
        f"{body_md}\n\n"
        f"---\n"
        f"Sent by Project Symphony, the GTM Intelligence + Action Layer at PureFacts.\n"
    )
    return html, plain


def send_email(
    *,
    gmail_address: str,
    gmail_app_password: str,
    to_email: str,
    subject: str,
    html_body: str,
    plain_body: str,
    from_name: str = "Project Symphony",
) -> None:
    """Send a multipart email via Gmail SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{gmail_address}>"
    msg["To"] = to_email
    msg["Reply-To"] = to_email
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    # 30s timeout: without it a flaky network can hang the whole Streamlit
    # rerun for minutes waiting on Gmail's SMTP. With the timeout the call
    # fails fast and the caller falls back to the in-app approve path.
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(gmail_address, gmail_app_password)
        smtp.send_message(msg)
