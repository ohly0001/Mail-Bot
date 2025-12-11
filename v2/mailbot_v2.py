from os import getenv
from dotenv import find_dotenv, load_dotenv
import atexit

from mailbot_logging import Logger
from mailbot_transformer import Transformer
from mailbot_mailing import Mail
from mailbot_db import DB

class MailBot:
    def __init__(self):
        self.logger = Logger(self)
        self.logger.info('Starting Up')
        
        self.transformer = None
        self.db = None
        self.mail = None
        
        atexit.register(self.close)
        
        path = find_dotenv()
        if not path:
            self.logger.error("Failed to find .env")
            exit(1)
        load_dotenv(path)
        
        # Measured in seconds
        self.followup_delay = float(getenv('FOLLOWUP_DELAY'))
        self.reply_throttle_delay = float(getenv('REPLY_THROTTLE_DELAY'))
        self.idle_delay = float(getenv('IDLE_DELAY'))
        
        model_params = {
            'model_path': getenv('MODEL_PATH'),
            'n_ctx': int(getenv('MODEL_CONTEXT_SIZE')),
            'n_threads': int(getenv('MODEL_THREAD_COUNT')),
            'n_gpu_layers': int(getenv('MODEL_GPU_LAYERS')),
            'stop': getenv('MODEL_END'),
            'verbose': bool(getenv('MODEL_VERBOSE'))
        }
        max_tokens = int(getenv('MODEL_MAX_OUTPUT_TOKENS'))
        self.transformer = Transformer(model_params, max_tokens)
        
        mysql_conn_params = {
            'host': getenv('MYSQL_HOST'),
            'user': getenv('MYSQL_USER'),
            'password': getenv('MYSQL_PASSWORD'),
            'database': getenv('MYSQL_DB')
        }
        self.db = DB(mysql_conn_params)
        registered_users = self.db.select_registered_users()
        
        mail_conn_params = {
            'imap_host': getenv('MAIL_IMAP_HOST'),
            'imap_user': getenv('MAIL_IMAP_USER'),
            'imap_password': getenv('MAIL_IMAP_PASSWORD'),
            'imap_inbox': getenv('MAIL_IMAP_INBOX'),
            'smtp_host': getenv('MAIL_SMTP_HOST'),
            'smtp_port': int(getenv('MAIL_SMTP_PORT')),
            'smtp_user': getenv('MAIL_SMTP_USER'),
            'smtp_password': getenv('MAIL_SMTP_PASSWORD')
        }
        self.mail = Mail(mail_conn_params, registered_users)
        
        self.logger.info('Running')
        self.logger.flush()
        
    def process_commands(self, email_address: str, body_text: str):
        for line in body_text.strip().split('\n'):
            if line.startswith('!'):
                cmd = line.removeprefix('!').strip().lower()
                if cmd == 'deregister': 
                    # Remove self from whitelist (equivelant to delete account)
                    self.db.delete_registered_user(email_address=email_address)
                    
                elif cmd in ['brief', 'stats']: 
                    # Get thread count, message count, (and other client details)
                    pass
                elif cmd in ['help', '?']: 
                    # Read user-level command list from help file 1 and send
                    pass
                
            elif line.startswith('/'):
                cmd = line.removeprefix('/').strip().lower()
                
                if cmd.startswith('mode') and cmd.endswith('natural', 'lazy', 'eager', 'idle'):
                    # Natrual: Respond only when a certain heuristic threshold is met (mimicking interest and converstional relevance)
                    # Lazy: Respond only when the bots name `Mistral` or a command is included
                    # Eager: Responds to every user thread received
                    # Idle: Don't respond but persist thread to db as received
                    # Idle: Ignore commands into switched from off to other mode
                    
                    mode = cmd.split(maxsplit=1)[1]
                    self.db.update_thread_bot_reply_mode(-1, mode)
                
                if cmd.startswith('filter'):
                    cmd = cmd.removeprefix('filter').strip()
                
                    if cmd.startswith('include'): #`me` is alias for self, `cc` is for all cc people, comma seperated, `all`` removes filtering
                        # Only responds to people in inclusion list, sets to thread whitelisting
                        pass
                    elif cmd.startswith('exclude'): #`me`` is alias for self, `cc` is for all cc people, comma seperated, `all`` removes filtering
                        # Only ignore people in exclusion list, sets to thread blacklisting (can be used to 'shun' cc recipients)
                        pass
                    
                # can also use: "Mistral, please provide a recap" etc, but this forces a particular response
                elif cmd == 'recap': 
                    # Request strict recap of conversation
                    pass
                elif cmd == 'summary': 
                    # Request condensed summary of conversation
                    pass
                elif cmd in ['brief', 'stats']: 
                    # Get token count and context window size, (and other details, like topic)
                    pass
                elif cmd in ['help', '?']: 
                    # Read thread-level command list from help file 2 and send
                    pass
        
    def close(self):
        self.logger.info("Shutting Down")
        
        if self.transformer:
            self.transformer.close()
        if self.db:
            self.db.close()
        if self.mail:
            self.mail.close()
        
        self.logger.info("Shut Down")
        self.logger.flush()

if __name__ == '__main__':
    mailbot = MailBot()
    