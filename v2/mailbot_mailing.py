from imaplib import IMAP4_SSL, IMAP4
from smtplib import SMTP_SSL, SMTPException
from email.message import EmailMessage
from email.utils import make_msgid, parseaddr, parsedate_to_datetime
from email.header import decode_header, make_header
from email import message_from_bytes
from dateutil.tz import tzlocal
from datetime import datetime

class Mail:
    def __init__(self, mail_conn_params, whitelist):
        self.mail_conn_params = mail_conn_params
        self.whitelist = tuple(row['whitelisted_address'] for row in whitelist)
        self.imap_conn = None
        self.smtp_conn = None

    # ------------------- Connection Helpers -------------------
    def connect_imap(self):
        try:
            self.imap_conn = IMAP4_SSL(self.mail_conn_params['imap_host'])
            self.imap_conn.login(self.mail_conn_params['imap_user'], self.mail_conn_params['imap_password'])
            self.imap_conn.select(self.mail_conn_params['imap_inbox'])
        except IMAP4.error as e:
            print(f"Failed to connect to IMAP: {e}")
            self.imap_conn = None

    def connect_smtp(self):
        try:
            self.smtp_conn = SMTP_SSL(self.mail_conn_params['smtp_host'], self.mail_conn_params['smtp_port'])
            self.smtp_conn.login(self.mail_conn_params['smtp_user'], self.mail_conn_params['smtp_password'])
        except SMTPException as e:
            print(f"Failed to connect to SMTP: {e}")
            self.smtp_conn = None

    def imap_call(self, func, *args, **kwargs):
        """Call IMAP with auto-reconnect on failure."""
        if not self.imap_conn:
            self.connect_imap()
        try:
            return func(*args, **kwargs)
        except IMAP4.error:
            print("IMAP connection lost. Reconnecting...")
            self.connect_imap()
            return func(*args, **kwargs)

    def smtp_call(self, func, *args, **kwargs):
        """Call SMTP with auto-reconnect on failure."""
        if not self.smtp_conn:
            self.connect_smtp()
        try:
            return func(*args, **kwargs)
        except SMTPException:
            print("SMTP connection lost. Reconnecting...")
            self.connect_smtp()
            return func(*args, **kwargs)
    
    # ------------------- Mail Operations -------------------
    
    def send_reply(self, original_email, rsp_text):
        pass

    def fetch_unread(self) -> list[dict]:
        messages = []
        
        status, data = self.imap_call(self.imap_conn.search, 'UNSEEN')

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
