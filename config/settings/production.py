import os
from .base import *
from dotenv import load_dotenv

load_dotenv(BASE_DIR/'.env')

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(',')
