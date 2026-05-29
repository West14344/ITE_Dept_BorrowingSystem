from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from borrowing import views as borrowing_views

urlpatterns = [
    path('admin/',  admin.site.urls),
    path('login/',  borrowing_views.login_view,  name='login'),
    path('logout/', borrowing_views.logout_view, name='logout'),
    path('',        borrowing_views.splash,       name='splash'),
    path('system/', include('borrowing.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)