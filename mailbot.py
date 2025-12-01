import os
import random
import time
from os import getenv
from dotenv import load_dotenv

from mailing import mail_controller
from persistence import db_controller
from transformer import ai_controller

# -------------------------
# Step 0: Initialization
# -------------------------
load_dotenv()

FAST_SCAN_INTERVAL = int(getenv('FAST_SCAN_INTERVAL'))  # e.g., 5 min
SLOW_SCAN_INTERVAL = int(getenv('SLOW_SCAN_INTERVAL'))  # e.g., 1 hour
MESSAGE_THROTTLING = int(getenv('MESSAGE_THROTTLING'))  # e.g., 12s per message (~5/min)

# -------------------------
# Step 0c: Load AI model
# -------------------------
print("Loading AI Model...")
MODEL_PARAMS = {
    'model_path': getenv('MODEL_PATH'),
    'n_ctx': int(getenv('MODEL_CONTEXT_SIZE')),
    'n_threads': int(getenv('MODEL_THREAD_COUNT')),
    'n_gpu_layers': int(getenv('MODEL_GPU_LAYERS')),
    'stop': getenv('MODEL_END'),
    'verbose': bool(getenv('MODEL_VERBOSE'))
}
MAX_OUT_TOKENS = int(getenv('MODEL_MAX_OUTPUT_TOKENS'))
transformer = ai_controller(MODEL_PARAMS, MAX_OUT_TOKENS)
print(f"Loaded Model ({os.path.basename(MODEL_PARAMS['model_path'])})!")

# -------------------------
# Step 0a: Connect to DB
# -------------------------
print("Connecting to MySQL DB...")
MYSQL_CONN_PARAMS = {
    'host': getenv('MYSQL_HOST'),
    'user': getenv('MYSQL_USER'),
    'password': getenv('MYSQL_PASSWORD'),
    'database': getenv('MYSQL_DB')
}
db = db_controller(MYSQL_CONN_PARAMS)
print("Connected to MySQL DB!")

# Fetch whitelist for inbox filtering
whitelist = db.select_whitelist()

# -------------------------
# Step 0b: Connect to Gmail
# -------------------------
print("Connecting to Gmail Servers...")
MAIL_CONN_PARAMS = {
    'imap_host': getenv('MAIL_IMAP_HOST'),
    'imap_user': getenv('MAIL_IMAP_USER'),
    'imap_password': getenv('MAIL_IMAP_PASSWORD'),
    'imap_inbox': getenv('MAIL_IMAP_INBOX'),
    'smtp_host': getenv('MAIL_SMTP_HOST'),
    'smtp_port': int(getenv('MAIL_SMTP_PORT')),
    'smtp_user': getenv('MAIL_SMTP_USER'),
    'smtp_password': getenv('MAIL_SMTP_PASSWORD')
}
mail = mail_controller(MAIL_CONN_PARAMS, whitelist)
print("Connected to Gmail Servers!")

# -------------------------
# Step 1: Main Loop
# -------------------------
try:
    while True:
        print("Fetching from Gmail Inbox...")
        inbox = mail.fetch_unread()
        inbox_size = len(inbox)

        if inbox_size > 0:
            # Step 2a: Persist incoming messages
            db.insert_emails(inbox)

            print(f"{inbox_size} email(s) received. Beginning batch processing...")
            for i, in_msg in enumerate(inbox, start=1):
                print(f"Processing email {i}/{inbox_size}")

                # Step 2b: Build conversation context
                msg_stack = db.select_email_thread(in_msg['email_parent_id'])
                msg_stack.append(in_msg)
                rsp_text = transformer(msg_stack)

                if not rsp_text:
                    print("No response generated. Skipping...")
                    continue

                # Step 2d: Send reply
                out_msg = mail.send_reply(in_msg, rsp_text)
                if out_msg:
                    # Step 2c: Persist reply
                    db.insert_email(out_msg)
                else:
                    print("Failed to send reply. Skipping persistence.")

                # Step 2e: Throttle to avoid spam limits
                print(f"Sleeping for {MESSAGE_THROTTLING}s before next reply...")
                # Random variation introduce to reduce bot blocking risk caused by exact intervals
                time.sleep(MESSAGE_THROTTLING + random.uniform(-1, 1))

            # Step 3: Short pause to check for quick follow-ups
            print(f"Batch complete. Sleeping for {FAST_SCAN_INTERVAL}s...")
            time.sleep(FAST_SCAN_INTERVAL + random.uniform(-10, 10))

        else:
            # Inbox empty → longer wait
            print(f"No messages received. Sleeping for {SLOW_SCAN_INTERVAL}s...")
            time.sleep(SLOW_SCAN_INTERVAL + random.uniform(-30, 30))

except KeyboardInterrupt:
    print("Terminating Mailbot...")