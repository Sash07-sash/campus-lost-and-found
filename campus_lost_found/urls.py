"""
URL configuration for campus_lost_found project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('items.urls')),
]

# Custom Error Handlers (Assessment Requirement)
handler404 = 'items.views.custom_404_view'
handler500 = 'items.views.custom_500_view'
handler403 = 'items.views.custom_403_view'
handler400 = 'items.views.custom_400_view'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Catch-all pattern to guarantee custom 404 page renders for any incorrect address
from django.urls import re_path
from items.views import custom_404_view
urlpatterns += [
    re_path(r'^.*$', custom_404_view),
]

