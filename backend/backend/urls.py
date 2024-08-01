from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import GoogleOauthSignInview,AdminLoginView,AdminHomeView,AdminLogoutApiView


urlpatterns = [
    path('google/', GoogleOauthSignInview.as_view(), name='google'),
    path('admin/', admin.site.urls),
    path('admin/logout/', AdminLogoutApiView.as_view(), name='admin-logout'),
    path('admin-login/',AdminLoginView.as_view()),
    path('admin-home/', AdminHomeView.as_view(), name='admin-home'),
    path('api/v1/auth/', include('accounts.urls')),
   

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
