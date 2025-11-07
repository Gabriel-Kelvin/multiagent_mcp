from typing import Dict, Any, List
import os
from app.logging_utils import JsonSqlLogger
from utils import sendgrid_utils


def run(state: Dict[str, Any], settings, logger: JsonSqlLogger) -> Dict[str, Any]:
    run_id = state.get("run_id", "")
    artifacts = state.get("artifacts") or {}
    csv_path = artifacts.get("csv_path")
    pdf_path = artifacts.get("pdf_path")
    to_emails: List[str] = []
    if getattr(settings, "EMAIL_TO", ""):
        to_emails = [e.strip() for e in settings.EMAIL_TO.split(",") if e.strip()]
    api_key = getattr(settings, "SENDGRID_API_KEY", "")
    from_email = getattr(settings, "EMAIL_FROM", "")
    # If config is missing, gracefully skip email instead of failing the whole run
    if not api_key or not to_emails or not from_email:
        logger.info(run_id, "email", "skipped", {"reason": "missing_email_config", "has_api_key": bool(api_key), "to_count": len(to_emails), "from": bool(from_email)})
        return {"status": "skipped", "data": {}, "log": {"reason": "missing_email_config"}}
    # Require artifacts to exist only if we are actually sending
    if not (csv_path and os.path.exists(csv_path)):
        logger.info(run_id, "email", "skipped", {"reason": "missing_csv", "csv_path": csv_path})
        return {"status": "skipped", "data": {}, "log": {"reason": "missing_csv"}}
    if not (pdf_path and os.path.exists(pdf_path)):
        logger.info(run_id, "email", "skipped", {"reason": "missing_pdf", "pdf_path": pdf_path})
        return {"status": "skipped", "data": {}, "log": {"reason": "missing_pdf"}}
    attachments = [
        {"file_path": csv_path, "mime_type": "text/csv", "file_name": os.path.basename(csv_path)},
        {"file_path": pdf_path, "mime_type": "application/pdf", "file_name": os.path.basename(pdf_path)},
    ]
    res = sendgrid_utils.send_email(
        subject="Multi-Agent Data Assistant Report",
        body_text=f"Report for: {state.get('user_input','')}",
        to_emails=to_emails,
        from_email=from_email,
        attachments=attachments,
        api_key=api_key,
    )
    status = res.get("status", "error")
    logger.info(run_id, "email", "email_done", {"status": status})
    return {"status": status, "data": {"email_result": res}, "log": {"status": status}}
