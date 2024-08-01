from django.urls import path
from .views import RegisterUserView, VerifyUserEmail, LoginUserView, TestAuthenticationView, PasswordResetRequestView, PasswordResetConfirm, SetNewPasswordView, LogoutApiView, RegisterRecruiterView,UserListView,RecruiterListView,JobListView,JobCreateView,create_company_profile,update_company_profile,get_company_profile,LogoutView, CreateJobView, PendingRecruitersView,check_company_profile,SkillListCreateAPIView,SkillDeleteAPIView,CheckUserProfileView, CreateUserProfileView,UserProfileView,UpdateUserProfileView,apply_job,get_job_applicants,download_resume,JobPostedList,CompanyListView,CompanyProfileDetailView,CompanyJobsView,suggested_jobs,CreateEducationView, CreateExperienceView,user_stats,get_notifications,mark_notifications_read,update_application_status,get_user_type,SkillUpdateAPIView,BlockUserView,UnblockUserView,BlockRecruiterView, UnblockRecruiterView,MonthlyUserStats
from rest_framework_simplejwt.views import TokenRefreshView
from accounts import views
from chat.views import get_chat_history,SendMessageView,create_chat_room,get_chat_room,get_chat_rooms,get_unread_message_counts,mark_messages_as_read




urlpatterns = [
    path('admin/logout/', LogoutView.as_view(), name='admin_logout'),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('verify-email/', VerifyUserEmail.as_view(), name='verify'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('profile/', TestAuthenticationView.as_view(), name='granted'),
    path('token/refresh/', TokenRefreshView.as_view(), name='refresh-token'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirm.as_view(), name='reset-password-confirm'),
    path('set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
    path('logout/', LogoutApiView.as_view(), name='logout'),
    path('recruiter/', RegisterRecruiterView.as_view(), name='register_recruiter'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('recruiters/', RecruiterListView.as_view(), name='recruiter-list'),
    path('jobs/', JobListView.as_view(), name='job-list'),
    path('job-posted/', JobPostedList.as_view(), name='job-lists'),
    path('jobs/create/', JobCreateView.as_view(), name='job-create'),
    path('admin/recruiters/pending/', PendingRecruitersView.as_view(), name='pending_recruiters'),
    path('admin/recruiters/pending/<int:recruiter_id>/', PendingRecruitersView.as_view(), name='approve_reject_recruiter'),
    path('company-profile/', create_company_profile, name='create_company_profile'),
    path('company-profile/update/<int:pk>/', update_company_profile, name='update_company_profile'),
    path('company-profile-get/', get_company_profile, name='get_company_profile'),
    path('jobs/create/', CreateJobView.as_view(), name='create-job'),
    path('api/jobs/', views.job_list, name='job-list'),
    path('check-company-profile/', check_company_profile, name='check_company_profile'),
    path('skills/', SkillListCreateAPIView.as_view(), name='skill-list-create'),
    path('api/jobs/<int:pk>/', views.job_detail, name='job-detail'),
    path('jobs/delete/<int:job_id>/', views.delete_job, name='delete_job'),
    path('company-profile-update/', views.update_company_about, name='update_company_about'),
    path('check-user-profile/', CheckUserProfileView.as_view(), name='check-user-profile'),
    path('create-user-profile/', CreateUserProfileView.as_view(), name='create-user-profile'),
    path('user-profile/', UserProfileView.as_view(), name='user-profile'),
    path('update-profile/', UpdateUserProfileView.as_view(), name='update-profile'),
    path('<int:job_id>/apply/', apply_job, name='update-profile'),
    path('<int:job_id>/applicants/', get_job_applicants, name='job_applicants'),
    path('download-resume/<str:application_id>/', download_resume, name='download_resume'),
    path('companies/', CompanyListView.as_view(), name='company-list'),
    path('company-profile-user/<int:pk>/', CompanyProfileDetailView.as_view(), name='company-profile-detail'),
    path('company-jobs/<int:company_id>/', CompanyJobsView.as_view(), name='company-jobs'),
    path('api/jobs/<int:job_id>/suggested/', suggested_jobs, name='suggested-jobs'),
    path('education/', CreateEducationView.as_view(), name='create-education'),
    path('education/<int:pk>/', CreateEducationView.as_view(), name='delete-education'),
    path('experience/', CreateExperienceView.as_view(), name='create-experience'),
    path('experience/<int:pk>/', CreateExperienceView.as_view(), name='experience-detail'),
    path('chat/history/<int:user_id>/', get_chat_history, name='chat_history'),
    path('chat/send/', SendMessageView.as_view(), name='send_message'),
    path('create-chat-room/', create_chat_room, name='create_chat_room'),
    path('chat-room/<int:room_id>/', get_chat_room, name='get_chat_room'),
    path('chat-rooms/', get_chat_rooms, name='get_chat_rooms'),
    path('api/user-stats/', user_stats, name='user_stats'),
    path('unread-message-counts/', get_unread_message_counts, name='unread-message-counts'),
    path('mark-messages-as-read/<int:room_id>/', mark_messages_as_read, name='mark-messages-as-read'),
    path('notifications/', get_notifications, name='get_notifications'),
    path('notifications/mark-read/', mark_notifications_read, name='mark_notifications_read'),
    path('update-application-status/', update_application_status, name='update_application_status'),
    path('user-type/', get_user_type, name='user-type'),
    path('skills-update/<int:pk>/', SkillUpdateAPIView.as_view(), name='skill-update'),
    path('skills/<int:pk>/', SkillDeleteAPIView.as_view(), name='skill-delete'),
    path('block-user/<int:user_id>/', BlockUserView.as_view(), name='block-user'),
    path('unblock-user/<int:user_id>/', UnblockUserView.as_view(), name='unblock-user'),
    path('block-recruiter/<int:recruiter_id>/', BlockRecruiterView.as_view(), name='block-recruiter'),
    path('unblock-recruiter/<int:recruiter_id>/', UnblockRecruiterView.as_view(), name='unblock-recruiter'),
    path('monthly-user-stats/', MonthlyUserStats.as_view(), name='monthly-user-stats'),




]
