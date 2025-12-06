import os
import random
import time
from os import getenv
from dotenv import find_dotenv, load_dotenv
import atexit

#from mailing_v2 import mail_controller
#from persistence_v2 import db_controller
from mailbot_logging import Logger
from mailbot_transformer import transformer

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
        
        self.transformer = transformer(model_params, max_tokens)
        
        atexit.register(self.close)
        
        self.logger.info('Running')
        self.logger.flush()
        
    def close(self):
        self.logger.info("Shutting Down")
        
        self.transformer.close()
        
        
        self.logger.info("Shut Down")
        self.logger.flush()

if __name__ == '__main__':
    mailbot = MailBot()
    