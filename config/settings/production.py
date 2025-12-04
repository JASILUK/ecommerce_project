import os
from .base import *
from dotenv import load_dotenv

load_dotenv(BASE_DIR/'.env')

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(',')

EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DEFAULT_FROM_EMAIL =os.getenv("DEFAULT_FROM_EMAIL")
EMAIL_USE_TLS =True
SENDGRID_SANDBOX_MODE_IN_DEBUG = False