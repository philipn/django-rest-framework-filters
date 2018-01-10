
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',

        'TEST': {
            'NAME': ':memory:',
        },
    },
}

MIDDLEWARE = []

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework_filters',
    'rest_framework',
    'django_filters',
    'tests.testapp',
)

SECRET_KEY = 'testsecretkey'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': True,
        },
    },
]


ROOT_URLCONF = 'tests.testapp.urls'

STATIC_URL = '/static/'
