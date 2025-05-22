from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# Django auth urls for login, logout, password reset/change
from app.views import login,logout_view

urlpatterns = [
    # ... other URL patterns ...
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('login/', login, name='login'),
    # Include the auth URLs for login, logout, password reset/change
    path('accounts/', include('django.contrib.auth.urls')),
    path('logout/', logout_view, name='logout'),
    # Include the auth URLs for login, logout, password reset/change
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)