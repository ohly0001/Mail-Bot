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
        
        atexit.register(self.close)
        
        self.logger.info('Running')
        self.logger.flush()
        
    def close(self):
        self.logger.info("Shutting Down")
        
        self.transformer.close()
        self.db.close()
        self.mail.close()
        
        self.logger.info("Shut Down")
        self.logger.flush()

if __name__ == '__main__':
    mailbot = MailBot()
    