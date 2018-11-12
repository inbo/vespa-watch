from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'vespa-watch',
        'HOST': 'localhost',
    }
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '<SOMETHING_SECRET_TO_REDEFINE_HERE>'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# INaturalist user information
INAT_USER_USERNAME = 'vespawatch'
INAT_USER_PASSWORD = ''
INAT_APP_ID = 'd1d0f541791be42e234ce82a5bb8332ab816ff7ab35c6e27b12c0455939a5ea8'
INAT_APP_SECRET = ''

# media file S3 static storage
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = None # None to use AWS internal role/permissions
AWS_ACCESS_KEY_ID = None
AWS_STORAGE_BUCKET_NAME = 'lw-vespawatch'
AWS_DEFAULT_ACL = None
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 1 day
}
AWS_S3_FILE_OVERWRITE = True
AWS_S3_REGION_NAME = ' eu-west-1'
AWS_LOCATION = 'media'