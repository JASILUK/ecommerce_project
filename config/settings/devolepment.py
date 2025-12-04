import os
from .base import *
from dotenv import load_dotenv

load_dotenv(BASE_DIR/'.env')

DEBUG = True
EMAIL_BACKEND=os.getenv("EMAIL_BACKEND")
EMAIL_HOST=os.getenv("EMAIL_HOST")
EMAIL_PORT=os.getenv("EMAIL_PORT")
EMAIL_USE_TLS=True
EMAIL_HOST_USER=os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL= os.getenv("DEFAULT_FROM_EMAIL")





CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": os.getenv("redispassword"),  
             "DECODE_RESPONSES": True,
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",

        }
    },
    "cart": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": os.getenv("redispassword"),  
             "DECODE_RESPONSES": True,
                "SERIALIZER": "django_redis.serializers.json.JSONSerializer",

        }
    }
}

