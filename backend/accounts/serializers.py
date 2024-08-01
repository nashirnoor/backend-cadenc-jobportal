from rest_framework import serializers
from .models import CompanyProfile,Skill,UserProfile,Education,Experience,User,Recruiter,UserProfile
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import smart_bytes, force_str
from django.urls import reverse
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .utils import Google, register_social_user,send_normal_email


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    password2 = serializers.CharField(max_length=68, min_length=6, write_only=True)
    phone_number = serializers.CharField(max_length=15, required=False)
    user_type = serializers.ChoiceField(choices=User.USER_TYPES, default='normal')

    class Meta:
        model = User
        fields = ['email', 'first_name', 'phone_number', 'password', 'password2', 'user_type']

    def validate(self, attrs):
        email = attrs.get('email')
        phone_number = attrs.get('phone_number')
        
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "This email already exists"})
        
        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError({"phone_number": "This phone number already exists"})
        
        password = attrs.get('password', '')
        password2 = attrs.get('password2', '')
        if password != password2:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        
        return attrs

    def create(self, validated_data):
        user_type = validated_data.pop('user_type', 'normal')
        if user_type == 'recruiter':
            recruiter = Recruiter.objects.create_user(
                email=validated_data['email'],
                first_name=validated_data.get('first_name'),
                phone_number=validated_data.get('phone_number'),
                company_name=validated_data.get('company_name'),
                password=validated_data.get('password')
            )
            return recruiter
        else:
            user = User.objects.create_user(
                email=validated_data['email'],
                first_name=validated_data.get('first_name'),
                phone_number=validated_data.get('phone_number'),
                password=validated_data.get('password')
            )
            return user
        


class RecruiterRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    password2 = serializers.CharField(max_length=68, min_length=6, write_only=True)
    phone_number = serializers.CharField(max_length=15, required=False)
    user_type = serializers.ChoiceField(choices=User.USER_TYPES, default='recruiter')
    company_name = serializers.CharField(max_length=255)

    class Meta:
        model = Recruiter
        fields = ['email', 'first_name', 'phone_number', 'company_name', 'password', 'password2', 'user_type']

    def validate(self, attrs):
        email = attrs.get('email')
        phone_number = attrs.get('phone_number')
        
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "This email already exists"})
        
        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError({"phone_number": "This phone number already exists"})
        
        password = attrs.get('password', '')
        password2 = attrs.get('password2', '')
        if password != password2:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        
        return attrs


    def create(self, validated_data):
        recruiter = Recruiter.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data.get('first_name'),
            phone_number=validated_data.get('phone_number'),
            company_name=validated_data.get('company_name'),
            password=validated_data.get('password')
        )
        return recruiter

class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=6)
    password = serializers.CharField(max_length=68, write_only=True)
    full_name = serializers.CharField(max_length=255, read_only=True)
    access_token = serializers.CharField(max_length=255, read_only=True)
    refresh_token = serializers.CharField(max_length=255, read_only=True)
    user_type = serializers.CharField(max_length=10, read_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'access_token', 'refresh_token', 'user_type']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        request = self.context.get('request')
        user = authenticate(request, email=email, password=password)
        if not user:
            raise AuthenticationFailed("Invalid credentials, try again")
        
        if user.user_type == 'recruiter' and not user.is_approved:
            raise AuthenticationFailed("Your account is not yet approved by the admin.")
        
        if not user.is_verified:
            raise AuthenticationFailed("Email is not verified")

        if user.is_blocked:
            raise AuthenticationFailed("Your account has been blocked. Please contact support.")

        user_tokens = user.tokens()
        return {
            'user': user,  # Add this line
            'email': user.email,
            'full_name': user.get_full_name,
            'access_token': str(user_tokens.get('access')),
            'refresh_token': str(user_tokens.get('refresh')),
            'user_type': user.user_type
        }
    
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        fields = ['email']

    def validate(self, attrs):
        
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            user= User.objects.get(email=email)
            uidb64=urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            request=self.context.get('request')
            current_site=get_current_site(request).domain
            
            relative_link =reverse('reset-password-confirm', kwargs={'uidb64':uidb64, 'token':token})
            abslink=f"http://localhost:5173{relative_link}"

            print(abslink)
            email_body=f"Hi {user.first_name} use the link below to reset your password {abslink}"
            data={
                'email_body':email_body, 
                'email_subject':"Reset your Password", 
                'to_email':user.email
                }
            send_normal_email(data)

        return super().validate(attrs)

class SetNewPasswordSerializer(serializers.Serializer):
    password=serializers.CharField(max_length=100, min_length=6, write_only=True)
    confirm_password=serializers.CharField(max_length=100, min_length=6, write_only=True)
    uidb64=serializers.CharField(min_length=1, write_only=True)
    token=serializers.CharField(min_length=3, write_only=True)

    class Meta:
        fields = ['password', 'confirm_password', 'uidb64', 'token']

    def validate(self, attrs):
        try:
            token=attrs.get('token')
            uidb64=attrs.get('uidb64')
            password=attrs.get('password')
            confirm_password=attrs.get('confirm_password')

            user_id=force_str(urlsafe_base64_decode(uidb64))
            user=User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed("reset link is invalid or has expired", 401)
            if password != confirm_password:
                raise AuthenticationFailed("passwords do not match")
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            return AuthenticationFailed("link is invalid or has expired")

class LogoutUserSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    default_error_messages={
        'bad_token':('Token is invalid or has expired')
    }

    def validate(self, attrs):
        self.token = attrs.get('refresh_token')
        return super().validate(attrs)
    
    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            return self.fail('bad_token')
        



class GoogleSignInSerializer(serializers.Serializer):
    access_token=serializers.CharField(min_length=6)

    def validate_access_token(self, access_token):
        user_data=Google.validate(access_token)
        try:
            user_id = user_data['sub']
            
        except:
            raise serializers.ValidationError("this token has expired or invalid please try again")
        
        if user_data['aud'] != settings.GOOGLE_CLIENT_ID:
                raise AuthenticationFailed(detail='Could not verify user.')

        email=user_data['email']
        first_name=user_data['given_name']
        # last_name=user_data['family_name']
        provider='google'

        return register_social_user(provider, email, first_name)



class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'is_staff', 'is_superuser', 'is_verified', 'is_active', 'date_joined', 'last_login','user_type','phone_number','is_blocked']

class RecruiterListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruiter
        fields = ['id', 'email', 'first_name', 'company_name', 'is_staff', 'is_superuser', 'is_verified', 'is_active', 'date_joined', 'last_login','user_type','is_blocked']



class CompanyProfileSerializer(serializers.ModelSerializer):
    job_count = serializers.SerializerMethodField()

    class Meta:
        model = CompanyProfile
        fields = ["id", "recruiter","about", "company_name", "company_location", "company_strength", "contact_number", "email_address", "company_logo","job_count"]
        read_only_fields = ['recruiter','job_count']

    def get_job_count(self, obj):
        return obj.job_count()

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'company_logo' and value is None:
                continue
            setattr(instance, attr, value)
        instance.save()
        return instance
    

class AdminLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=6)
    password = serializers.CharField(max_length=68, write_only=True)
    full_name = serializers.CharField(max_length=255, read_only=True)
    access_token = serializers.CharField(max_length=255, read_only=True)
    refresh_token = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'access_token', 'refresh_token']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        request = self.context.get('request')
        user = authenticate(request, email=email, password=password)
        if not user:
            raise AuthenticationFailed("Invalid credentials, try again")
        if not user.is_verified:
            raise AuthenticationFailed("Email is not verified")
        if not user.is_superuser:
            raise AuthenticationFailed("You do not have admin privileges")
        user_tokens = user.tokens()

        return {
            'email': user.email,
            'full_name': user.get_full_name,
            'access_token': str(user_tokens.get('access')),
            'refresh_token': str(user_tokens.get('refresh')),
        }



from .models import Job
class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']


class JobSerializer(serializers.ModelSerializer):
    company_logo = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    applicants_count = serializers.IntegerField(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = Job
        fields = [
            'id', 'recruiter', 'job_title', 'job_type', 'salary', 
            'vacancies', 'experience', 'job_location', 'job_description', 
            'core_responsibilities', 'created_at', 'updated_at', 'company_logo',
            'company_name', 'deleted', 'applicants_count','skills', 'skill_ids','job_location_type'
        ]
        read_only_fields = ['recruiter', 'created_at', 'updated_at']
        

    def get_applicants_count(self, obj):
        return len(obj.applications)  

    def get_company_logo(self, obj):
        try:
            company_profile = CompanyProfile.objects.get(recruiter=obj.recruiter)
            if company_profile.company_logo:
                return self.context['request'].build_absolute_uri(company_profile.company_logo.url)
        except CompanyProfile.DoesNotExist:
            pass
        return None

    def get_company_name(self, obj):
        try:
            company_profile = CompanyProfile.objects.get(recruiter=obj.recruiter)
            return company_profile.company_name
        except CompanyProfile.DoesNotExist:
            return None
    def create(self, validated_data):
        skill_ids = validated_data.pop('skill_ids', [])
        job = Job.objects.create(**validated_data)
        job.skills.set(Skill.objects.filter(id__in=skill_ids))
        return job

    def update(self, instance, validated_data):
        skill_ids = validated_data.pop('skill_ids', None)
        job = super().update(instance, validated_data)
        if skill_ids is not None:
            job.skills.set(Skill.objects.filter(id__in=skill_ids))
        return job



class UserProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    about = serializers.CharField(max_length=800, required=False)

    class Meta:
        model = UserProfile
        fields = ['photo', 'skills', 'resume', 'full_name', 'email', 'position', 'about']

    def get_full_name(self, obj):
        return obj.user.get_full_name

    def get_email(self, obj):
        return obj.user.email

    def update(self, instance, validated_data):
        instance.about = validated_data.get('about', instance.about)
        instance.save()
        return instance
    

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = '__all__'
    
