import json
from channels.generic.websocket import AsyncWebsocketConsumer

class QueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'queue_updates'

        # Join the shared queue updates broadcast group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive broadcast from Django channel layer and push down to React client
    async def queue_event(self, event):
        await self.send(text_data=json.dumps(event['payload']))
