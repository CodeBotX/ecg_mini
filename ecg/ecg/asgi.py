# """
# ASGI config for ecg project.

# It exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
# """

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecg.settings')

# application = get_asgi_application()


"""
ecg/asgi.py

ASGI entrypoint cho dự án.  
• HTTP → Django view.  
• WebSocket → Channels routing.
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# Quan trọng: trỏ tới settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecg.settings")
django.setup()                     # cần khi kết hợp Channels + Django

# ---- Django HTTP ----
django_app = get_asgi_application()

# ---- WebSocket routing ----
from live.routing import websocket_urlpatterns   # import sau khi django.setup()

application = ProtocolTypeRouter(
    {
        # HTTP requests
        "http": django_app,

        # WebSocket kết hợp session / user auth
        "websocket": AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    }
)
