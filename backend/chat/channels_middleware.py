from channels.middleware import BaseMiddleware
from channels.exceptions import DenyConnection
from channels.db import database_sync_to_async
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import close_old_connections
import urllib.parse
User = get_user_model()

class JWTWebsocketMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        print("Middleware called")
        print(f"Scope: {scope}")
        close_old_connections()
        
        query_string = scope.get("query_string", b"").decode("utf-8")
        print(f"Query string: {query_string}")
        
        token = None
        if "token=" in query_string:
            token = query_string.split("token=")[1].split("&")[0]
            token = urllib.parse.unquote(token).strip('"')
        print(f"Received token: {token}")
        print(f"Extracted token: {token}")

        if token is None:
            print("No token provided")
            raise DenyConnection()

        try:
            payload = decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get('user_id')
            
            if user_id is None:
                print("No user_id in token payload")
                raise DenyConnection()

            user = await self.get_user(user_id)
            if user is None:
                print("User not found")
                raise DenyConnection()

            print(f"Authenticated user: {user}")
            scope['user'] = user

        except ExpiredSignatureError:
            print("Token expired")
            raise DenyConnection()

        except InvalidTokenError:
            print("Invalid token")
            raise DenyConnection()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None