from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import *

# ------------------------------------------------------------------
# DRF router
# ------------------------------------------------------------------
router = DefaultRouter()


# ------------------------------------------------------------------
# URL patterns
# ------------------------------------------------------------------
app_name = "ecg_app"                         


urlpatterns = [
    # ---------- REST API (cho ESP32 / mobile app) ----------
    path("api/",        include((router.urls, "api"))),      # /api/...
    path("api-auth/",   include("rest_framework.urls")),     # login browsable API
    path("device/<str:device_id>/recording/", RecordingToggleAPIView.as_view()),

    # ---------- Auth ----------
    path("login/",      login_view,    name="login"),
    path("register/",   register_view, name="register"),
    path("logout/",     logout_view,   name="logout"),

    # ---------- Trang chính ----------
    path("",            home_view,                 name="home"),
    path("devices/",    device_management_view,    name="device_management"),
    path("history/",    measurement_history_view,  name="history"),

    # ---------- Hồ sơ / bệnh án ----------
    path("profile/",                    profile_view,          name="profile"),
    path("profile/medical-history/",    medical_history_view,  name="medical_history"),
    path("profile/medications/",        medication_view,       name="medications"),
    path("profile/upload-image/",       upload_profile_image,  name="upload_profile_image"),
    path("profile/remove-image/",       remove_profile_image,  name="remove_profile_image"),
    path("profile/edit/",               edit_profile_view,       name="edit_profile"),

    # ---------- Device Management ----------
    path('monitor/', monitor_list_view, name='monitor_list'),  # LIST trước
    path('monitor/<str:device_id>/', monitor_view, name='monitor'),  # DETAIL sau
    path('delete-measurement/', delete_measurement, name='delete_measurement'),
    path('add-device/', add_device, name='add_device'),
    path('edit-device/', edit_device, name='edit_device'),
    path('delete-device/', delete_device, name='delete_device'),

    # Medical History URLs
    path('profile/medical-history/add/', add_medical_history, name='add_medical_history'),
    path('profile/medical-history/<int:history_id>/edit/', edit_medical_history, name='edit_medical_history'),
    path('profile/medical-history/<int:history_id>/delete/', delete_medical_history, name='delete_medical_history'),
    
    # Medication URLs
    path('profile/medication/add/', add_medication, name='add_medication'),
    path('profile/medication/<int:medication_id>/edit/', edit_medication, name='edit_medication'),
    path('profile/medication/<int:medication_id>/delete/', delete_medication, name='delete_medication'),
]

# ------------------------------------------------------------------
# Media files (chỉ hoạt động ở chế độ DEBUG)
# ------------------------------------------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
