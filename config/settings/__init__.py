import os

from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT_SETTING = os.getenv("DJANGO_ENV","development") 
if ENVIRONMENT_SETTING =='production' :
    from .production import *
else:
    from .devolepment import *