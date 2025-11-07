import base64
import os
from typing import List, Dict, Any, Optional


def send_email(subject: str, body_text: str, to_emails: List[str], from_email: str, attachments: Optional[List[Dict[str, str]]] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    if not api_key or not to_emails or not from_email:
        return {"status": "skipped", "log": {"reason": "missing_config"}}
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
        message = Mail(
            from_email=from_email,
            to_emails=to_emails,
            subject=subject,
            plain_text_content=body_text,
        )
        for att in attachments or []:
            path = att.get("file_path")
            if not path or not os.path.exists(path):
                continue
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            a = Attachment(
                FileContent(encoded),
                FileName(att.get("file_name") or os.path.basename(path)),
                FileType(att.get("mime_type") or "application/octet-stream"),
                Disposition("attachment"),
            )
            message.add_attachment(a)
        sg = SendGridAPIClient(api_key=api_key)
        resp = sg.send(message)
        return {"status": "success", "data": {"status_code": resp.status_code}}
    except Exception as e:
        return {"status": "error", "log": {"error": str(e)}}
