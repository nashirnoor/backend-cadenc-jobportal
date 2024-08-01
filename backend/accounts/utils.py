import random
from django.core.mail import EmailMessage
from .models import User, OneTimePassword
from django.conf import settings
# google
from google.auth.transport import requests
from google.oauth2 import id_token
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed


from django.utils import timezone

def generateOtp():
    otp = ""
    for i in range(6):
        otp += str(random.randint(1, 9))
    return otp

def send_code_to_user(email):
    Subject = "One time passcode for Email verification"
    otp_code = generateOtp()
    print(otp_code)
    user = User.objects.get(email=email)
    current_site = "myAuth.com"
    email_body = f"Hi {user.first_name}, thanks for signing up on {current_site}. Please verify your email with this one-time passcode: {otp_code}"
    from_email = settings.DEFAULT_FROM_EMAIL

    OneTimePassword.objects.update_or_create(user=user, defaults={'code': otp_code, 'created_at': timezone.now()})

    d_email = EmailMessage(subject=Subject, body=email_body, from_email=from_email, to=[email])
    d_email.send(fail_silently=True)

def send_normal_email(data):
    email = EmailMessage(
        subject=data['email_subject'],
        body=data['email_body'],
        from_email=settings.EMAIL_HOST_USER,
        to=[data['to_email']]
    )
    email.send()



#google

class Google():
    @staticmethod
    def validate(access_token):
        try:
            id_info=id_token.verify_oauth2_token(access_token, requests.Request())
            if 'accounts.google.com' in id_info['iss']:
                return id_info
        except Exception as e:
            return "the token is either invalid or has expired"


def login_user(email,password):
    user = authenticate(email=email, password=password)
    user_tokens = user.tokens()
    return {
        'email':user.email,
        'full_name':user.get_full_name,
        'access_token':str(user_tokens.get('access')),
        'refresh_token':str(user_tokens.get('refresh'))

    }



def register_social_user(provider, email, first_name):
    user=User.objects.filter(email=email)
    if user.exists():
        if provider == user[0].auth_provider:
            login_user(email, settings.SOCIAL_AUTH_PROVIDER)
        else:
            raise AuthenticationFailed(
                detail=f"please continue your login with {user[0].auth_provider}"
            )
    else:
        new_user={
            'email':email,
            'first_name':first_name,
            'password':settings.SOCIAL_AUTH_PASSWORD
        }
        register_user=User.objects.create_user(**new_user)
        register_user.auth_provider=provider
        register_user.is_verified=True
        register_user.save()
        login_user(email=register_user.email,password=settings.SOCIAL_AUTH_PASSWORD)
       