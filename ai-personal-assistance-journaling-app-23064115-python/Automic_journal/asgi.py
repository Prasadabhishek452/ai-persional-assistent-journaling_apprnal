import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import Apps.Chatbot.rountings as route

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Automic_journal.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': URLRouter(route.websocket_router)
})
