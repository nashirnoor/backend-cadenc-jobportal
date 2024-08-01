from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .manager import UserManager
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import uuid
from django.contrib.auth import get_user_model


AUTH_PROVIDERS = {'email':'email', 'google':'google'}

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Skill Name"))

    def __str__(self):
        return self.name

class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ('normal', 'Normal User'),
        ('recruiter', 'Recruiter'),
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    email = models.EmailField(max_length=255, unique=True, verbose_name=_("Email Address"))
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True, verbose_name=_("Phone Number"))
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)        
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    auth_provider = models.CharField(max_length=50, default="email")
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='normal')
    skills = models.ManyToManyField(Skill, related_name="users", blank=True, verbose_name=_("Skills"))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def get_full_name(self):
        return self.first_name  

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

class Recruiter(User):
    company_name = models.CharField(max_length=255, verbose_name=_("Company Name"))
    
    def save(self, *args, **kwargs):
        self.user_type = 'recruiter'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Recruiter")
        verbose_name_plural = _("Recruiters")


class CompanyProfile(models.Model):
    recruiter = models.OneToOneField(Recruiter, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=255, verbose_name=_("Company Name"))
    about = models.CharField(max_length=1000, verbose_name=_("About"), blank=True)
    company_location = models.CharField(max_length=255, verbose_name=_("Company Location"))
    company_strength = models.CharField(max_length=255, verbose_name=_("Company Strength"))
    contact_number = models.CharField(max_length=15, verbose_name=_("Contact Number"))
    email_address = models.EmailField(max_length=255, verbose_name=_("Email Address"))
    company_logo = models.ImageField(upload_to='company_logos/', null=True, blank=True, verbose_name=_("Company Logo"))

    def __str__(self):
        return self.company_name
    
    def job_count(self):
        return Job.objects.filter(recruiter=self.recruiter, deleted=False).count()

    class Meta:
        verbose_name = _("Company Profile")
        verbose_name_plural = _("Company Profiles")



class OneTimePassword(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True) 

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=1)

    def __str__(self):
        return f"{self.user.first_name}-passcode"

    
User = get_user_model()

class Job(models.Model):
    JOB_TYPES = (
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
    )

    JOB_LOCATION_TYPES = (
        ('on_site', 'On-site'),
        ('hybrid', 'Hybrid'),
        ('remote', 'Remote'),
    )

    APPLICATION_STATUS = (
        ('pending', 'Pending'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('await', 'Await'),
    )

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_posts')
    job_title = models.CharField(max_length=255, verbose_name=_("Job Title"))
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, verbose_name=_("Job Type"))
    salary = models.CharField(max_length=255, verbose_name=_("Salary"))
    vacancies = models.PositiveIntegerField(verbose_name=_("No. of Vacancies"))
    experience = models.CharField(max_length=255, verbose_name=_("Experience"))
    job_location = models.CharField(max_length=255, verbose_name=_("Job Location"))
    job_description = models.TextField(verbose_name=_("Job Description"))
    core_responsibilities = models.TextField(verbose_name=_("Core Responsibilities"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    applications = models.JSONField(default=list)
    deleted = models.BooleanField(default=False, verbose_name=_("Deleted"))  # New field
    skills = models.ManyToManyField('Skill', related_name='user_jobs', blank=True, verbose_name=_("Skills"))
    job_location_type = models.CharField(max_length=20, choices=JOB_LOCATION_TYPES, default='on_site', verbose_name=_("Job Location Type"))
    applications = models.JSONField(default=list)

    class Meta:
        unique_together = ['recruiter', 'job_title']

    def __str__(self):
        return self.job_title
    
    def update_application_status(self, applicant_id, status):
        for app in self.applications:
            if app['id'] == applicant_id:
                app['status'] = status
                break
        self.save()
    


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    position = models.CharField(max_length=255, verbose_name=_("Position"), blank=True)
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True, verbose_name=_("Profile Photo"))
    skills = models.ManyToManyField('Skill', related_name='user_profiles', blank=True, verbose_name=_("Skills"))
    resume = models.FileField(upload_to='resumes/', null=True, blank=True, verbose_name=_("Resume"))
    about = models.CharField(max_length=800,verbose_name=_("about_user"), blank=True)

    def __str__(self):
        return f"Profile of {self.user.email}"

class Education(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='educations')
    university = models.CharField(max_length=255, verbose_name=_("University"))
    degree = models.CharField(max_length=100, verbose_name=_("Degree"))
    field_of_study = models.CharField(max_length=100, verbose_name=_("Field of Study"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"), null=True, blank=True)

    def __str__(self):
        return f"{self.degree} in {self.field_of_study} at {self.university} ({self.user_profile.user.email})"

class Experience(models.Model):
    EMPLOYMENT_TYPES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('self_employed', 'Self-Employed'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
        ('trainee', 'Trainee'),
    )
    
    LOCATION_TYPES = (
        ('on_site', 'On-Site'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
    )
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user_experiences')
    title = models.CharField(max_length=100, verbose_name=_("Title"))
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, verbose_name=_("Employment Type"))
    location_type = models.CharField(max_length=10, choices=LOCATION_TYPES, verbose_name=_("Location Type"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"), null=True, blank=True)
    role = models.CharField(max_length=100, verbose_name=_("Role"))

    def __str__(self):
        return f"{self.title} at {self.user_profile.user.email}"
    

class AdminNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.message