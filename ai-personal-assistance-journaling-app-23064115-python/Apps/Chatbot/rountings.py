from django.urls import path
from Apps.Chatbot.consumers import MyAsyncJsonWebsocketConsumer, AsyncSocketVision,AsyncSocketDairy

websocket_router = [
    path("test/", MyAsyncJsonWebsocketConsumer.as_asgi()),
    path("vision/", AsyncSocketVision.as_asgi()),
    path("dairy/", AsyncSocketDairy.as_asgi()),
   
]
