"""
ASGI config for queue_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'queue_backend.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing routing or consumers
django_asgi_app = get_asgi_application()

import api.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(api.routing.websocket_urlpatterns),
})
