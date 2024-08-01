from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from chat.serializer import MessageSerializer
from rest_framework.response import Response
from accounts.models import User
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import ChatMessage
from rest_framework.views import APIView
from rest_framework import status
from .models import ChatMessage
from .serializer import ChatMessage
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ChatMessage,ChatRoom
from .serializer import MessageSerializer


class SendMessageView(APIView):
    def post(self, request):
        sender = request.user
        receiver_id = request.data.get('receiver_id')
        content = request.data.get('message', '')
        file = request.FILES.get('file')
        image = request.FILES.get('image')

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({"error": "Receiver not found"}, status=status.HTTP_404_NOT_FOUND)

        message = ChatMessage.objects.create(
            sender=sender,
            receiver=receiver,
            content=content,
            file=file,
            image=image,
            is_read = False
        )

        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_history(request, user_id):
    messages = ChatMessage.objects.filter(
        (Q(sender=request.user, receiver_id=user_id) | 
         Q(sender_id=user_id, receiver=request.user))
    ).order_by('date')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_chat_room(request):
    applicant_id = request.data.get('applicant_id')
    try:
        applicant = User.objects.get(id=applicant_id)
        chat_room, created = ChatRoom.objects.get_or_create(
            user1=request.user,
            user2=applicant
        )
        return Response({
            'room_id': chat_room.id,
            'other_user': {
                'id': applicant.id,
                'first_name': applicant.first_name,
                'email': applicant.email,
                'profile_photo': applicant.profile.photo.url if applicant.profile.photo else None,
            }
        })
    except User.DoesNotExist:
        return Response({'error': 'Applicant not found'}, status=404)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_room(request, room_id):
    try:
        chat_room = ChatRoom.objects.get(id=room_id)
        other_user = chat_room.user2 if chat_room.user1 == request.user else chat_room.user1
        return Response({
            'room_id': chat_room.id,
            'other_user': {
                'id': other_user.id,
                'first_name': other_user.first_name,
                'email': other_user.email,
                'profile_photo': other_user.profile_photo.url if other_user.profile_photo else None,
            }
        })
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Chat room not found'}, status=404)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_rooms(request):
    chat_rooms = ChatRoom.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    data = []
    for room in chat_rooms:
        other_user = room.user2 if room.user1 == request.user else room.user1
        last_message = room.messages.order_by('-date').first()
        
        
        profile_photo = None
        if hasattr(other_user, 'profile') and other_user.profile:
            profile_photo = other_user.profile.photo.url if other_user.profile.photo else None
        
        data.append({
            'id': room.id,
            'other_user': {
                'id': other_user.id,
                'first_name': other_user.first_name,
                'email': other_user.email,
                'profile_photo': profile_photo,
            },
            'last_message': last_message.content if last_message else None,
            'last_message_date': last_message.date if last_message else None,
        })
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_messages(request, room_id):
    try:
        chat_room = ChatRoom.objects.get(id=room_id)
        messages = ChatMessage.objects.filter(chat_room=chat_room).order_by('date')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Chat room not found'}, status=404)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_message_counts(request):
    chat_rooms = ChatRoom.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    unread_counts = {}
    for room in chat_rooms:
        other_user = room.user2 if room.user1 == request.user else room.user1
        unread_count = ChatMessage.objects.filter(
            chat_room=room,
            receiver=request.user,
            is_read=False
        ).count()
        unread_counts[room.id] = {
            'count': unread_count,
            'other_user_id': other_user.id
        }
    return Response(unread_counts)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_as_read(request, room_id):
    ChatMessage.objects.filter(
        chat_room_id=room_id,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)
    return Response({'status': 'success'})

