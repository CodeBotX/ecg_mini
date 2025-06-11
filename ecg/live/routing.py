# live/routing.py
from django.urls import re_path
from .consumers import ECGUploadConsumer, ECGMonitorConsumer

websocket_urlpatterns = [
    re_path(r"ws/device/(?P<device_id>\w+)/upload/$",  ECGUploadConsumer.as_asgi()),
    re_path(r"ws/monitor/(?P<device_id>\w+)/$",        ECGMonitorConsumer.as_asgi()),
]
