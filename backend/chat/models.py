from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import User

User = get_user_model()

class ChatRoom(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_rooms_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_rooms_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message = models.ForeignKey('ChatMessage', related_name='last_message_for_room', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('user1', 'user2')

class ChatMessage(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.CharField(max_length=1000)
    is_read = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)

    class Meta:
        ordering = ['date']
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.sender} - {self.receiver}"

    @property
    def sender_profile(self):
        return self.sender

    @property
    def receiver_profile(self):
        return self.receiver