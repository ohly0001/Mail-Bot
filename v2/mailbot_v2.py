import os
import random
import time
from os import getenv
from dotenv import load_dotenv

from mailing_v2 import mail_controller
from v1.persistence import db_controller
from v1.transformer import ai_controller

def startup():
    load_dotenv()
    
    