"""
WSGI config for the52club project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the52club.settings')
application = get_wsgi_application()
