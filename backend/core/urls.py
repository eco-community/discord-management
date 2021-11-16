"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path
from django.conf import settings
from django.contrib import admin
from django.conf.urls import include

urlpatterns = [
    path("grappelli/", include("grappelli.urls")),  # grappelli URLS
    path("", admin.site.urls),  # admin site
]

admin.site.index_title = f"{settings.PROJECT_NAME} Discord"
admin.site.site_url = None


if settings.DEBUG:
    import debug_toolbar

    urlpatterns.append(
        path("__debug__/", include(debug_toolbar.urls)),
    )
