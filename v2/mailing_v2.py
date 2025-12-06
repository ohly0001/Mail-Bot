from imaplib import IMAP4_SSL, IMAP4
from smtplib import SMTP_SSL, SMTPException
from email.message import EmailMessage
from email.utils import make_msgid, parseaddr, parsedate_to_datetime
from email.header import decode_header, make_header
from email import message_from_bytes
from dateutil.tz import tzlocal
from datetime import datetime

class mail_controller:
    def __init__(self, mail_conn_params, whitelist):
        self.mail_conn_params = mail_conn_params
        self.whitelist = tuple(row['whitelisted_address'] for row in whitelist)
        self.imap_conn = None
        self.smtp_conn = None
        self._connect_imap()
        self._connect_smtp()

    # ------------------- Connection Helpers -------------------
    def _connect_imap(self):
        try:
            self.imap_conn = IMAP4_SSL(self.mail_conn_params['imap_host'])
            self.imap_conn.login(self.mail_conn_params['imap_user'], self.mail_conn_params['imap_password'])
            self.imap_conn.select(self.mail_conn_params['imap_inbox'])
        except IMAP4.error as e:
            print(f"Failed to connect to IMAP: {e}")
            self.imap_conn = None

    def _connect_smtp(self):
        try:
            self.smtp_conn = SMTP_SSL(self.mail_conn_params['smtp_host'], self.mail_conn_params['smtp_port'])
            self.smtp_conn.login(self.mail_conn_params['smtp_user'], self.mail_conn_params['smtp_password'])
        except SMTPException as e:
            print(f"Failed to connect to SMTP: {e}")
            self.smtp_conn = None

    def _imap_call(self, func, *args, **kwargs):
        """Call IMAP command with auto-reconnect on failure."""
        if not self.imap_conn:
            self._connect_imap()
        try:
            return func(*args, **kwargs)
        except IMAP4.error:
            print("IMAP connection lost. Reconnecting...")
            self._connect_imap()
            return func(*args, **kwargs)

    def _smtp_call(self, func, *args, **kwargs):
        """Call SMTP command with auto-reconnect on failure."""
        if not self.smtp_conn:
            self._connect_smtp()
        try:
            return func(*args, **kwargs)
        except SMTPException:
            print("SMTP connection lost. Reconnecting...")
            self._connect_smtp()
            return func(*args, **kwargs)

    # ------------------- Mail Operations -------------------
    def send_reply(self, original_email, rsp_text):
        msg = EmailMessage()
        msg["To"] = original_email["sender_address"]
        msg["From"] = self.mail_conn_params["smtp_user"]
        subject = original_email['subject_line']
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        msg["Subject"] = subject
        msg["In-Reply-To"] = original_email["email_id"]
        refs = original_email.get("references")
        msg["References"] = f"{refs} {original_email['email_id']}" if refs else original_email["email_id"]
        msg["Message-ID"] = make_msgid()
        msg.set_content(rsp_text)

        # 1. Send via SMTP
        self._smtp_call(self.smtp_conn.send_message, msg)

        # 2. Append to Sent Mail
        raw_message = msg.as_bytes()
        result = self._imap_call(
            self.imap_conn.append,
            '"[Gmail]/Sent Mail"',
            '\\Seen',
            datetime.now(tzlocal()),
            raw_message
        )

        # UID extraction (optional, keeps your original logic)
        sent_uid = 0
        if result[0] == 'OK' and result[1]:
            resp = result[1][0].decode()
            if resp.startswith("APPENDUID"):
                try:
                    sent_uid = int(resp.split()[2])
                except (IndexError, ValueError):
                    pass

        return {
            "email_uid": sent_uid,
            "email_parent_id": original_email["email_id"],
            "email_id": msg["Message-ID"],
            "subject_line": subject,
            "sender_name": "Mistral AI",
            "sender_address": self.mail_conn_params['smtp_user'],
            "body_text": rsp_text,
            "sent_on": datetime.now(tzlocal())
        }

    def fetch_unread(self) -> list[dict]:
        messages = []
        status, data = self._imap_call(self.imap_conn.search, None, 'UNSEEN')
        if status != 'OK':
            return messages

        for num in data[0].split():
            status, msg_data = self._imap_call(self.imap_conn.fetch, num, '(RFC822 UID)')
            if status != 'OK':
                continue
            raw_email = msg_data[0][1]
            msg = message_from_bytes(raw_email)

            # Mark as seen
            try:
                self._imap_call(self.imap_conn.store, num, '+FLAGS.SILENT', '\\Seen')
            except IMAP4.error:
                pass

            sender_name, sender_email = parseaddr(msg.get("From"))
            sender_email = sender_email.lower()
            if sender_email not in self.whitelist:
                continue

            # UID extraction
            uid = None
            for part in msg_data:
                if isinstance(part, tuple):
                    resp = part[0].decode()
                    if "UID " in resp:
                        try:
                            uid = int(resp.split("UID ", 1)[1].split()[0])
                        except ValueError:
                            uid = None
                        break
            if uid is None:
                continue

            # Body extraction (plain text)
            body = None
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                        body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore').strip()
                        break
            elif msg.get_content_type() == "text/plain":
                body = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='ignore').strip()
            if body is None:
                continue

            subject_raw = msg.get("Subject") or ""
            subject = str(make_header(decode_header(subject_raw)))
            message_id = msg.get("Message-ID")
            parent_id = msg.get("In-Reply-To")
            sending_time = None
            try:
                sending_time = parsedate_to_datetime(msg.get("Date"))
            except Exception:
                sending_time = datetime.now(tzlocal())

            messages.append({
                "email_uid": uid,
                "email_parent_id": parent_id,
                "email_id": message_id,
                "subject_line": subject,
                "sender_name": sender_name,
                "sender_address": sender_email,
                "body_text": body,
                "sent_on": sending_time
            })

        return messages

    def close(self):
        try:
            if self.imap_conn:
                self.imap_conn.close()
                self.imap_conn.logout()
            if self.smtp_conn:
                self.smtp_conn.quit()
        except Exception:
            pass
        print("Disconnected from Gmail servers")
