from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile, ECGData

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(ECGData)
class ECGDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'sample_rate')
    list_filter = ('user', 'timestamp')
    search_fields = ('user__username', 'user__email')
    date_hierarchy = 'timestamp'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
