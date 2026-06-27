"""
Email Skill — sends rejection notifications via SMTP.
Called automatically by ApprovalGate on every REJECT action.
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

REJECT_RECIPIENTS = [
    "suwitchan.c@tidlor.com",
    "napat.wa@tidlor.com",
]


def send_rejection_email(
    stage: int,
    stage_name: str,
    project: str,
    version: str,
    jira: str,
    reason: str,
    approver: str,
    run_id: str,
) -> bool:
    """
    Send rejection notification email.
    Returns True if sent, False if SMTP not configured (logs warning instead).
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    sender    = os.getenv("SMTP_FROM", smtp_user or "qa-agent@noreply.com")

    subject = f"[QA REJECTED] {project} v{version} — Stage {stage}: {stage_name} ({jira})"
    html = _build_html(stage, stage_name, project, version, jira, reason, approver, run_id)
    text = _build_text(stage, stage_name, project, version, jira, reason, approver, run_id)

    if not all([smtp_host, smtp_user, smtp_pass]):
        # SMTP not configured — print to console instead
        print(f"\n{'='*55}")
        print(f"  📧 [EMAIL] Rejection notification (SMTP not configured)")
        print(f"  To      : {', '.join(REJECT_RECIPIENTS)}")
        print(f"  Subject : {subject}")
        print(f"  Reason  : {reason}")
        print(f"{'='*55}\n")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = sender
        msg["To"]      = ", ".join(REJECT_RECIPIENTS)
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html",  "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(sender, REJECT_RECIPIENTS, msg.as_string())

        print(f"  📧 Rejection email sent → {', '.join(REJECT_RECIPIENTS)}")
        return True

    except Exception as e:
        print(f"  ⚠️  Email failed: {e}")
        return False


def _build_html(stage, stage_name, project, version, jira, reason, approver, run_id):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f8fafc; margin: 0; padding: 0; }}
  .wrap {{ max-width: 580px; margin: 32px auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 16px rgba(0,0,0,.08); }}
  .header {{ background: #1e1b4b; padding: 28px 32px; }}
  .header-badge {{ display: inline-flex; align-items: center; gap: 8px; background: #ef444420; border: 1px solid #ef444455; border-radius: 20px; padding: 4px 14px; margin-bottom: 12px; }}
  .header-badge span {{ color: #f87171; font-size: 12px; font-weight: 700; letter-spacing: .5px; }}
  .header h1 {{ color: #fff; font-size: 20px; margin: 0; font-weight: 700; }}
  .header p {{ color: #a5b4fc; font-size: 13px; margin: 6px 0 0; }}
  .body {{ padding: 28px 32px; }}
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }}
  .info-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 14px; }}
  .info-label {{ font-size: 10px; color: #94a3b8; text-transform: uppercase; letter-spacing: .7px; margin-bottom: 4px; }}
  .info-value {{ font-size: 14px; font-weight: 600; color: #1e293b; }}
  .stage-box {{ background: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px; padding: 14px 16px; margin-bottom: 20px; }}
  .stage-label {{ font-size: 11px; color: #c2410c; font-weight: 700; margin-bottom: 4px; }}
  .stage-value {{ font-size: 15px; font-weight: 700; color: #ea580c; }}
  .reason-box {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; margin-bottom: 20px; }}
  .reason-label {{ font-size: 11px; color: #b91c1c; font-weight: 700; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }}
  .reason-text {{ font-size: 14px; color: #7f1d1d; line-height: 1.6; }}
  .action-box {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px 16px; margin-bottom: 24px; }}
  .action-label {{ font-size: 11px; color: #166534; font-weight: 700; margin-bottom: 6px; }}
  .action-list {{ font-size: 13px; color: #14532d; line-height: 1.8; }}
  .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 32px; font-size: 11px; color: #94a3b8; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="header-badge"><span>❌ QA PIPELINE REJECTED</span></div>
    <h1>{project} v{version}</h1>
    <p>Run: {run_id} · {jira} · {ts}</p>
  </div>
  <div class="body">
    <div class="info-grid">
      <div class="info-box"><div class="info-label">Run ID</div><div class="info-value">{run_id}</div></div>
      <div class="info-box"><div class="info-label">Jira Issue</div><div class="info-value">{jira}</div></div>
      <div class="info-box"><div class="info-label">Project</div><div class="info-value">{project} v{version}</div></div>
      <div class="info-box"><div class="info-label">Rejected By</div><div class="info-value">{approver}</div></div>
    </div>
    <div class="stage-box">
      <div class="stage-label">REJECTED AT STAGE</div>
      <div class="stage-value">Stage {stage}: {stage_name}</div>
    </div>
    <div class="reason-box">
      <div class="reason-label">❌ Reason for Rejection</div>
      <div class="reason-text">{reason}</div>
    </div>
    <div class="action-box">
      <div class="action-label">📋 Required Actions</div>
      <div class="action-list">
        1. Review the rejection reason above<br>
        2. Address the issues in Jira: {jira}<br>
        3. Re-trigger the QA pipeline when ready<br>
        4. Notify {approver} when resolved
      </div>
    </div>
  </div>
  <div class="footer">
    Sent automatically by QA Workflow Agent · ProjectQA · {ts}
  </div>
</div>
</body>
</html>"""


def _build_text(stage, stage_name, project, version, jira, reason, approver, run_id):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""
QA PIPELINE REJECTED
====================
Project  : {project} v{version}
Run ID   : {run_id}
Jira     : {jira}
Rejected : Stage {stage} — {stage_name}
By       : {approver}
Time     : {ts}

REASON:
{reason}

REQUIRED ACTIONS:
1. Review the rejection reason above
2. Address the issues in Jira: {jira}
3. Re-trigger the QA pipeline when ready
4. Notify {approver} when resolved

--
Sent automatically by QA Workflow Agent
"""
