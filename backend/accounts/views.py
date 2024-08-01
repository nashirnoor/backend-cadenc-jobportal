from rest_framework.generics import GenericAPIView
from .serializers import UserRegisterSerializer,LoginSerializer,PasswordResetRequestSerializer, SetNewPasswordSerializer,LogoutUserSerializer, GoogleSignInSerializer,RecruiterRegisterSerializer,CompanyProfileSerializer,SkillSerializer
from rest_framework import status
from .utils import send_code_to_user
from .models import OneTimePassword,CompanyProfile, UserProfile
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .models import User,Recruiter
from rest_framework.generics import GenericAPIView
from .serializers import UserListSerializer, RecruiterListSerializer
from rest_framework.permissions import IsAdminUser
from rest_framework import generics
from .models import Skill
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .serializers import RecruiterListSerializer 
from rest_framework.views import APIView
from .utils import send_normal_email  
from rest_framework.permissions import BasePermission
from rest_framework import generics
from .models import User
from django.db.models import Count
from django.db import IntegrityError
from rest_framework import status
from rest_framework.views import APIView
from .models import UserProfile, Skill
from .serializers import UserProfileSerializer
import json
from .serializers import EducationSerializer, ExperienceSerializer
from .serializers import AdminLoginSerializer
from rest_framework.views import APIView
from rest_framework import generics, permissions
from .models import Job
from .serializers import JobSerializer
from rest_framework.permissions import IsAuthenticated
from .models import Job
from django.http import HttpResponse
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import time
from django.core.files.storage import default_storage
import os
import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .models import Experience,Education
from django.http import JsonResponse
from django.db.models import Count
from .models import User,Job
from django.utils import timezone
from django.db.models import Count, functions as F
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAdminUser



def user_stats(request):
    total_users = User.objects.count()
    total_recruiters = User.objects.filter(user_type='recruiter').count()
    total_normal_users = User.objects.filter(user_type='normal').count()
    total_posts = Job.objects.count()

    return JsonResponse({
        'totalUsers': total_users,
        'totalRecruiters': total_recruiters,
        'totalNormalUsers': total_normal_users,
        'totalPosts': total_posts
    })


class MonthlyUserStats(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        current_year = timezone.now().year

        monthly_data = User.objects.filter(
            date_joined__year=current_year
        ).annotate(
            month=F.ExtractMonth('date_joined')
        ).values(
            'month'
        ).annotate(
            count=Count('id')
        ).order_by('month')

        data = [0] * 12
        for entry in monthly_data:
            data[entry['month'] - 1] = entry['count']

        return Response(data)

from .models import AdminNotification

class RegisterUserView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    def post(self, request):
        user_data = request.data
        serializer = self.serializer_class(data=user_data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            AdminNotification.objects.create(
                user=user,
                message=f"New user registered: {user.email}"
            )
            send_code_to_user(user.email)

            return Response({
                'data': serializer.data,
                'message': 'Hi, thanks for signing up. A passcode has been sent to your email.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    
class RegisterRecruiterView(GenericAPIView):
    serializer_class = RecruiterRegisterSerializer

    def post(self, request):
        recruiter_data = request.data
        serializer = self.serializer_class(data=recruiter_data)
        if serializer.is_valid(raise_exception=True):
            recruiter = serializer.save()
            AdminNotification.objects.create(
                user=recruiter,
                message=f"New recruiter registered: {recruiter.email}"
            )
            send_mail(
                'New Recruiter Registration',
                f'A new recruiter has registered with email {recruiter.email}. Please review and approve or reject the registration.',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            return Response({
                'data': serializer.data, 
                'message': 'Registration successful. An admin will review your request.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PendingRecruitersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        pending_recruiters = Recruiter.objects.filter(is_approved=False)
        serializer = RecruiterListSerializer(pending_recruiters, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, recruiter_id):
        action = request.data.get('action')
        try:
            recruiter = Recruiter.objects.get(id=recruiter_id, is_approved=False)
            if action == 'approve':
                recruiter.is_approved = True
                recruiter.is_verified = True  
                recruiter.save()
                
                email_body = f"Hi {recruiter.first_name}, your recruiter account has been approved. You can now log in using the following link: http://localhost:5173/login"
                email_data = {
                    'email_subject': 'Recruiter Account Approved',
                    'email_body': email_body,
                    'to_email': recruiter.email,
                }
                send_normal_email(email_data)
                
                return Response({'message': 'Recruiter approved'}, status=status.HTTP_200_OK)
            elif action == 'reject':
                email_body = f"Hi {recruiter.first_name}, we regret to inform you that your recruiter account has been rejected."
                email_data = {
                    'email_subject': 'Recruiter Account Rejected',
                    'email_body': email_body,
                    'to_email': recruiter.email,
                }
                send_normal_email(email_data)
                
                recruiter.delete()
                return Response({'message': 'Recruiter rejected'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
        except Recruiter.DoesNotExist:
            return Response({'error': 'Recruiter not found'}, status=status.HTTP_404_NOT_FOUND)

    

class VerifyUserEmail(GenericAPIView):
    def post(self, request):
        otp_code = request.data.get('otp')
        try:
            user_code_obj = OneTimePassword.objects.get(code=otp_code)
            if user_code_obj.is_expired():
                return Response({'message': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = user_code_obj.user
            if not user.is_verified:
                user.is_verified = True
                user.save()
                return Response({
                    'message': "Account email verified successfully"
                }, status=status.HTTP_200_OK)
            return Response({
                'message': 'Code is invalid. User already verified'
            }, status=status.HTTP_204_NO_CONTENT)
        except OneTimePassword.DoesNotExist:
            return Response({'message': 'Invalid OTP'}, status=status.HTTP_404_NOT_FOUND)


class LoginUserView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class TestAuthenticationView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data={
            'msg':'its works'
        }
        return Response(data, status=status.HTTP_200_OK)
    

class PasswordResetRequestView(GenericAPIView):
    serializer_class=PasswordResetRequestSerializer

    def post(self, request):
        serializer=self.serializer_class(data=request.data, context={'request':request})
        serializer.is_valid(raise_exception=True)
        return Response({'message':'we have sent you a link to reset your password'}, status=status.HTTP_200_OK)

class PasswordResetConfirm(GenericAPIView):
    def get(self, request, uidb64, token):
        try:
            user_id=smart_str(urlsafe_base64_decode(uidb64))
            user=User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({'message':'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({'success':True, 'message':'credentials is valid', 'uidb64':uidb64, 'token':token}, status=status.HTTP_200_OK)

        except DjangoUnicodeDecodeError as identifier:
            return Response({'message':'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)

class SetNewPasswordView(GenericAPIView):
    serializer_class=SetNewPasswordSerializer

    def patch(self, request):
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success':True, 'message':"password reset is succesful"}, status=status.HTTP_200_OK)


class LogoutApiView(GenericAPIView):
    serializer_class=LogoutUserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

    
class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser

class AdminLogoutApiView(GenericAPIView):
    serializer_class = LogoutUserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GoogleOauthSignInview(GenericAPIView):
    serializer_class=GoogleSignInSerializer

    def post(self, request):
        print(request.data)
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data=((serializer.validated_data)['access_token'])
        return Response(data, status=status.HTTP_200_OK) 
    
    
    
class UserPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserListView(generics.ListAPIView):
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = UserPagination

    def get_queryset(self):
        return User.objects.filter(user_type='normal')
    


class BlockUserView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.is_blocked = True
            user.save()
            return Response({"message": "User blocked successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class UnblockUserView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.is_blocked = False
            user.save()
            return Response({"message": "User unblocked successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class BlockRecruiterView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, recruiter_id):
        try:
            recruiter = Recruiter.objects.get(id=recruiter_id)
            recruiter.is_blocked = True
            recruiter.save()
            return Response({"message": "Recruiter blocked successfully"}, status=status.HTTP_200_OK)
        except Recruiter.DoesNotExist:
            return Response({"error": "Recruiter not found"}, status=status.HTTP_404_NOT_FOUND)

class UnblockRecruiterView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, recruiter_id):
        try:
            recruiter = Recruiter.objects.get(id=recruiter_id)
            recruiter.is_blocked = False
            recruiter.save()
            return Response({"message": "Recruiter unblocked successfully"}, status=status.HTTP_200_OK)
        except Recruiter.DoesNotExist:
            return Response({"error": "Recruiter not found"}, status=status.HTTP_404_NOT_FOUND)



class CustomPaginationrecruiter(PageNumberPagination):
    page_size = 8
    page_size_query_param = 'page_size'
    max_page_size = 50

class RecruiterListView(generics.ListAPIView):
    queryset = Recruiter.objects.all()
    serializer_class = RecruiterListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPaginationrecruiter

  
class AdminLoginView(GenericAPIView):
    serializer_class = AdminLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class AdminHomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            return Response({"detail": "You do not have permission to access this resource."}, status=status.HTTP_403_FORBIDDEN)
        return Response({"message": "Welcome to the admin home page."}, status=status.HTTP_200_OK)



class JobCreateView(generics.CreateAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(recruiter=self.request.user)

class JobListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Job.objects.filter(recruiter=self.request.user, deleted=False)
    
class JobPostedList(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Job.objects.filter(recruiter=self.request.user)
    
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    



@api_view(['GET'])
def job_list(request):
    job_title = request.query_params.get('job_title', '')
    job_location = request.query_params.get('job_location', '')

    jobs = Job.objects.all().order_by('-created_at').filter(deleted=False)
    print(jobs)

    if job_title:
        jobs = jobs.filter(job_title__icontains=job_title)
    if job_location:
        jobs = jobs.filter(job_location__icontains=job_location)

    paginator = StandardResultsSetPagination()
    result_page = paginator.paginate_queryset(jobs, request)
    serializer = JobSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)



@api_view(['GET'])
def job_detail(request, pk):
    try:
        job = Job.objects.get(pk=pk)
    except Job.DoesNotExist:
        return Response(status=404)
    
    serializer = JobSerializer(job, context={'request': request})
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_job(request, job_id):
    try:
        job = Job.objects.get(id=job_id, recruiter=request.user)
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    job.deleted = True
    job.save()
    return Response({"message": "Job unlisted successfully"}, status=status.HTTP_204_NO_CONTENT)



@api_view(['GET'])
def suggested_jobs(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=404)

    job_skills = job.skills.all()
    similar_jobs = Job.objects.filter(skills__in=job_skills).exclude(id=job_id).distinct()
    similar_jobs = similar_jobs.annotate(matching_skills=Count('skills')).order_by('-matching_skills')
    similar_jobs = similar_jobs[:6]
    serializer = JobSerializer(similar_jobs, many=True, context={'request': request})
    return Response(serializer.data)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_company_profile(request):
    user = request.user
    print(request.data)
    print(user.user_type)

    if user.user_type != 'recruiter':
        return Response({'error': 'Only recruiters can create a company profile.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        recruiter = Recruiter.objects.get(id=user.id) 
    except Recruiter.DoesNotExist:
        return Response({'error': 'Recruiter profile does not exist.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CompanyProfileSerializer(data=request.data)

    if serializer.is_valid():
        company_profile = serializer.save(recruiter=recruiter)
        return Response(CompanyProfileSerializer(company_profile).data, status=status.HTTP_201_CREATED)
    
    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CompanyListView(APIView):
    def get(self, request):
        companies = CompanyProfile.objects.all()
        serializer = CompanyProfileSerializer(companies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CompanyProfileDetailView(APIView):
    def get(self, request, pk):
        try:
            company = CompanyProfile.objects.get(pk=pk)
            serializer = CompanyProfileSerializer(company)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CompanyProfile.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        

import logging

logger = logging.getLogger(__name__)

class CompanyJobsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        try:
            company_profile = CompanyProfile.objects.get(id=company_id)
            logger.info(f"CompanyProfile found: {company_profile}")

            jobs = Job.objects.filter(recruiter=company_profile.recruiter, deleted=False)
            logger.info(f"Number of jobs found: {jobs.count()}")

            serializer = JobSerializer(jobs, many=True, context={'request': request})
            logger.info(f"Serialized data: {serializer.data}")

            return Response(serializer.data, status=status.HTTP_200_OK)
        except CompanyProfile.DoesNotExist:
            logger.warning(f"CompanyProfile with id {company_id} not found")
            return Response({'error': 'Company profile not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in CompanyJobsView: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_company_profile(request, pk):
    try:
        company_profile = CompanyProfile.objects.get(pk=pk)
    except CompanyProfile.DoesNotExist:
        return Response({'error': 'Company profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    print("Received data:", request.data)
    print("Files:", request.FILES)

    serializer = CompanyProfileSerializer(company_profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    print("Serializer errors:", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company_profile(request):
    try:
        if not hasattr(request.user, 'recruiter'):
            return Response({'error': 'User has no recruiter profile.'}, status=status.HTTP_404_NOT_FOUND)

        company_profile = CompanyProfile.objects.get(recruiter=request.user.recruiter)
        serializer = CompanyProfileSerializer(company_profile)
        return Response(serializer.data)
    except CompanyProfile.DoesNotExist:
        return Response({'error': 'Company profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_company_about(request):
    try:
        company_profile = CompanyProfile.objects.get(recruiter=request.user.recruiter)
    except CompanyProfile.DoesNotExist:
        return Response({"error": "Company profile not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = CompanyProfileSerializer(company_profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#Adminu Logout
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


class CreateJobView(APIView):
    def post(self, request):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            try:
                job = serializer.save(recruiter=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                print(f"IntegrityError: {str(e)}")  
                return Response(
                    {"error": "You have already posted a job with this title."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        print(f"Serializer errors: {serializer.errors}")  
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        jobs = Job.objects.filter(recruiter=request.user)
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)

    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_company_profile(request):
    try:
        if not hasattr(request.user, 'recruiter'):
            return Response(status=status.HTTP_204_NO_CONTENT)

        company_profile = CompanyProfile.objects.get(recruiter=request.user.recruiter)
        return Response(status=status.HTTP_200_OK)
    except CompanyProfile.DoesNotExist:
        return Response(status=status.HTTP_204_NO_CONTENT)

    

class CustomPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 100

class SkillListCreateAPIView(APIView):
    pagination_class = CustomPagination

    def get(self, request):
        search_query = request.query_params.get('search', '')
        skills = Skill.objects.filter(name__icontains=search_query)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(skills, request)
        serializer = SkillSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = SkillSerializer(data=request.data)
        if serializer.is_valid():
            skill_name = serializer.validated_data['name']
            existing_skill = Skill.objects.filter(name=skill_name).first()
            if existing_skill:
                return Response({'error': 'Skill already exists'}, status=status.HTTP_409_CONFLICT)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class SkillUpdateAPIView(APIView):
    def put(self, request, pk):
        try:
            skill = Skill.objects.get(pk=pk)
        except Skill.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = SkillSerializer(skill, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SkillDeleteAPIView(APIView):
    def delete(self, request, pk):
        try:
            skill = Skill.objects.get(pk=pk)
        except Skill.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        skill.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class CheckUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            UserProfile.objects.get(user=request.user)
            return Response(status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            print("Page Doesn't exist")
            return Response(status=status.HTTP_204_NO_CONTENT)
    


class CreateUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        print(user)

        if hasattr(user, 'profile'):
            return Response({"detail": "User profile already exists."}, status=status.HTTP_400_BAD_REQUEST)

        skill_ids = request.data.get('skills', [])
        skill_ids = json.loads(skill_ids)
        skills = Skill.objects.filter(id__in=skill_ids)

        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save(user=user)
            profile.skills.set(skills)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class CreateEducationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_profile = request.user.profile
        data = request.data.copy()
        data['user_profile'] = user_profile.id
        serializer = EducationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        user_profile = request.user.profile
        educations = Education.objects.filter(user_profile=user_profile)
        serializer = EducationSerializer(educations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk=None):
        user_profile = request.user.profile
        try:
            education = Education.objects.get(pk=pk, user_profile=user_profile)
            education.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Education.DoesNotExist:
            return Response({'error': 'Education not found or not authorized to delete this education'}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, pk=None):
        if pk is None:
            return Response({'error': 'Education ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_profile = request.user.profile
        try:
            education = Education.objects.get(pk=pk, user_profile=user_profile)
            data = request.data.copy()
            data['user_profile'] = user_profile.id
            serializer = EducationSerializer(education, data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Education.DoesNotExist:
            return Response({'error': 'Education not found or not authorized to edit this education'}, status=status.HTTP_404_NOT_FOUND)


class CreateExperienceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_profile = request.user.profile
        data = request.data.copy()
        data['user_profile'] = user_profile.id
        serializer = ExperienceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        user_profile = request.user.profile
        experiences = Experience.objects.filter(user_profile=user_profile)
        serializer = ExperienceSerializer(experiences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk=None):
        user_profile = request.user.profile
        try:
            experience = Experience.objects.get(pk=pk, user_profile=user_profile)
        except Experience.DoesNotExist:
            return Response({'error': 'Experience not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ExperienceSerializer(experience, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk=None):
        user_profile = request.user.profile
        try:

            experience = Experience.objects.get(pk=pk, user_profile=user_profile)
        except Experience.DoesNotExist:
            return Response({'error': 'Experience not found'}, status=status.HTTP_404_NOT_FOUND)

        experience.delete()
        return Response({'message': 'Experience deleted'}, status=status.HTTP_204_NO_CONTENT)

    

class UserProfileView(APIView):

    def get(self, request):
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            print(user_profile)
            serializer = UserProfileSerializer(user_profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({"detail": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)
        

class UpdateUserProfileView(generics.UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_job(request, job_id):
    user = request.user
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({'error': 'Job not found'}, status=404)
    
    resume_file = request.FILES.get('resume')
    if resume_file:
        filename = f"resume_{user.id}_{job_id}_{int(time.time())}{os.path.splitext(resume_file.name)[1]}"
        file_path = default_storage.save(f'resumes/{filename}', resume_file)
        resume_url = default_storage.url(file_path)
    else:
        resume_url = None

    application = {
        'id': str(uuid.uuid4()),  
        'user_id': user.id,
        'is_immediate_joinee': request.data.get('isImmediateJoinee'),
        'experience': request.data.get('experience'),
        'is_willing_to_relocate': request.data.get('isWillingToRelocate'),
        'resume_url': resume_url,
    }

    job.applications.append(application)
    job.save()

    return Response({'message': 'Application submitted successfully'}, status=201)

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_type(request):
    return Response({'user_type': request.user.user_type})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_applicants(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
        
        for app in job.applications:
            user = User.objects.get(id=app['user_id'])
            app['id'] = user.id  # Use the user's ID instead of generating a new UUID
            app['username'] = user.get_full_name
            app['phone_number'] = user.phone_number
            app['email'] = user.email
        
        job.save()
        
        return Response(job.applications, status=200)
    except Job.DoesNotExist:
        return Response({'error': 'Job not found'}, status=404)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_application_status(request):
    applicant_id = request.data.get('applicant_id')
    job_id = request.data.get('job_id')
    status = request.data.get('status')

    try:
        job = Job.objects.get(id=job_id)
        job.update_application_status(applicant_id, status)
        return Response({'message': 'Status updated successfully'}, status=200)
    except Job.DoesNotExist:
        return Response({'error': 'Job not found'}, status=404)
    

    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_resume(request, application_id):
    try:
        print(f"Searching for application with ID: {application_id}")
        job = Job.objects.filter(applications__contains=[{'id': application_id}]).first()
        if not job:
            print(f"No job found containing application with ID: {application_id}")
            return Response({"error": "Job not found"}, status=404)
        
        application = next((app for app in job.applications if app['id'] == application_id), None)
        if not application:
            print(f"Application with ID {application_id} not found in job")
            return Response({"error": "Application not found"}, status=404)
        
        resume_url = application.get('resume_url')
        if not resume_url:
            print(f"No resume URL found for application {application_id}")
            return Response({"error": "Resume URL not found"}, status=404)
        
        print(f"Attempting to download resume from URL: {resume_url}")
        response = requests.get(resume_url)
        print(f"Cloudinary response status code: {response.status_code}")
        
        if response.status_code == 200:
            django_response = HttpResponse(response.content, content_type='application/pdf')
            django_response['Content-Disposition'] = f'attachment; filename="resume_{application_id}.pdf"'
            return django_response
        else:
            return Response({"error": "File not found on Cloudinary"}, status=404)
    
    except Exception as e:
        print(f"Error in download_resume: {str(e)}")
        return Response({"error": str(e)}, status=500)
    


# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    notifications = AdminNotification.objects.filter(is_read=False)
    data = {
        'user_count': notifications.filter(user__user_type='normal').count(),
        'recruiter_count': notifications.filter(user__user_type='recruiter').count(),
    }
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notifications_read(request):
    user_type = request.data.get('user_type')
    AdminNotification.objects.filter(user__user_type=user_type, is_read=False).update(is_read=True)
    return Response({'status': 'success'})