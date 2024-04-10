import os
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Recife'
USE_I18N = True
USE_L10N = True
USE_TZ = False
STATIC_ROOT = 'static'
STAIC_URL = 'static/'
MEDIA_ROOT = 'media'
MEDIA_URL = 'media/'
SITE_URL = 'http://localhost:8000'
ALLOWED_HOSTS = ['*']
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = 'ALLOWALL'

DECIMAL_SEPARATOR = ','
USE_THOUSAND_SEPARATOR = False

LOGGING_ = {
    'version': 1,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}

_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/var/tmp/cache",
    }
}

if os.environ.get('REDIS_HOST'):
    REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
    REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
  
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "master/{}:{}/0".format(REDIS_HOST, REDIS_PORT),
            "OPTIONS": {
                "PASSWORD": REDIS_PASSWORD,
                "ALWAYS_MASTER": True,
                "CLIENT_CLASS": "pnp.redis.PNPRedisClient",
                "SENTINEL_TIMEOUT": 3
            }
        }
    }


if os.environ.get('POSTGRES_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ.get('DATABASE_NAME', 'database'),
            'USER': os.environ.get('DATABASE_USER', 'postgres'),
            'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'password'),
            'HOST': os.environ.get('DATABASE_HOST', 'postgres'),
            'PORT': os.environ.get('DATABASE_PORT', '5432'),
        }
    }


