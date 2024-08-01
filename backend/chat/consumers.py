from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .models import ChatMessage
from accounts.models import User
from django.utils import timezone  

class PersonalChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        request_user = self.scope['user']
        if request_user.is_authenticated:
            room_id = self.scope['url_route']['kwargs']['room_id']
            self.room_group_name = f"chat_{room_id}"
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
        await self.accept()

    @database_sync_to_async
    def save_message(self, sender, receiver, content, file=None, image=None):
        message = ChatMessage.objects.create(
            sender=sender,
            receiver=receiver,
            content=content,
            file=file,
            image=image,
            is_read=False
        )
        return message

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message = data.get("message", "")
        sender = self.scope['user']
        receiver_id = int(self.scope['url_route']['kwargs']['id'])
        receiver = await self.get_user(receiver_id)

        if receiver is None:
            await self.send(text_data=json.dumps({
                "error": f"User with id {receiver_id} does not exist."
            }))
            return

        saved_message = await self.save_message(sender, receiver, message)
        file_url = self.scope['request'].build_absolute_uri(saved_message.file.url) if saved_message.file else None
        image_url = self.scope['request'].build_absolute_uri(saved_message.image.url) if saved_message.image else None

        await self.channel_layer.group_send(
         self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "user_id": sender.id,
                "file_url": file_url,
                "image_url": image_url,
            }
        )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def chat_message(self, event):
        message = event['message']
        timestamp = timezone.now().isoformat()
        await self.send(text_data=json.dumps({
            "message": message,
            "sent": event['user_id'] == self.scope['user'].id,
            "date": timestamp,
            "file_url": event.get('file_url'),
            "image_url": event.get('image_url'),
        }))