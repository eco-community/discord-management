from django.conf import settings


def admin_media(request):
    return {"ADMIN_LOGO_URL": settings.ADMIN_LOGO_URL}
