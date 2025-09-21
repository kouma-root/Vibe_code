"""
WebSocket URL routing for the finflow application.

This module defines the WebSocket URL patterns and routes them to the appropriate consumers.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Portfolio price feed WebSocket endpoint
    re_path(r'ws/portfolio/$', consumers.PortfolioConsumer.as_asgi()),
    
    # You can add more WebSocket routes here in the future
    # re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    # re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
