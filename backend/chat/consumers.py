from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .models import ChatMessage
from accounts.models import User
from django.utils import timezone
from django.conf import settings
import logging
import base64
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

class PersonalChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # No room group; accept the connection directly
        await self.accept()
        print(f"User {self.scope['user'].id} connected")
        await self.channel_layer.group_add(
        'chat_all',  # Ensure this group name matches
        self.channel_name
)

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
        try:
            data = json.loads(text_data)
            message = data.get("message", "")
            sender = self.scope['user']
            receiver_id = data.get('receiver_id')
            receiver = await self.get_user(receiver_id)

            if not receiver:
                await self.send(text_data=json.dumps({
                    "error": f"User with id {receiver_id} does not exist."
                }))
                return

            file = None
            image = None

            if 'file' in data:
                file_data = data['file']
                file_content = base64.b64decode(file_data['data'])
                file = ContentFile(file_content, name=file_data['name'])

            if 'image' in data:
                image_data = data['image']
                image_content = base64.b64decode(image_data['data'])
                image = ContentFile(image_content, name=image_data['name'])

            saved_message = await self.save_message(sender, receiver, message, file, image)

            file_url = f"{settings.MEDIA_URL}{saved_message.file.name}" if saved_message.file else None
            image_url = f"{settings.MEDIA_URL}{saved_message.image.name}" if saved_message.image else None

            await self.channel_layer.group_send(
                'chat_all',
                {
                    "type": "chat_message",
                    "message": message,
                    "user_id": sender.id,
                    "file_url": file_url,
                    "image_url": image_url,
                }
            )
        except Exception as e:
            logger.error(f"Error in receive method: {str(e)}")

    async def chat_message(self, event):
        message = event['message']
        print(f"chat_message received event: {event}")  # Debug log
        timestamp = timezone.now().isoformat()
        print(f"Sending message to WebSocket: {message}")  # Debug log
        await self.send(text_data=json.dumps({
            "message": message,
            "sent": event['user_id'] == self.scope['user'].id,
            "date": timestamp,
            "file_url": event.get('file_url'),
            "image_url": event.get('image_url'),
        }))



    async def disconnect(self, code):
        print(f"User {self.scope['user'].id} disconnected")
        # No room group to discard
        await self.close()
