"""
ASGI config for the52club project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the52club.settings')
application = get_asgi_application()
