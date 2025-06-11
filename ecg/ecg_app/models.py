from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField  # Nếu dùng Django 3.1+ và không dùng PostgreSQL

# Hồ sơ người dùng, chứa thông tin bệnh lý
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    blood_type = models.CharField(max_length=5, blank=True)
    height = models.FloatField(null=True, blank=True)  # in cm
    weight = models.FloatField(null=True, blank=True)  # in kg
    heart_disease_history = models.TextField(blank=True)
    medications = models.TextField(blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['user']  # Đặt mặc định sắp xếp theo user
        db_table = 'user_profile'  # Tùy chỉnh tên bảng trong DB
        indexes = [
            models.Index(fields=['user']),  # Index hóa trường 'user' để tối ưu truy vấn
        ]

class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_name = models.CharField(max_length=100)
    device_id = models.CharField(max_length=100, unique=True)
    device_type = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_connected = models.DateTimeField(auto_now=True)
    recording   = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.device_name} ({self.device_id})"

# Dữ liệu ECG: lưu theo batch JSON array
class ECGData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(verbose_name='Recording Time')
    sample_rate = models.IntegerField(default=200, verbose_name='Sample Rate (Hz)')
    data = JSONField(verbose_name='ECG Data')

    def __str__(self):
        return f"ECG Recording ({len(self.data)} samples) by {self.user.username} @ {self.timestamp}"

    class Meta:
        verbose_name = 'ECG Recording'
        verbose_name_plural = 'ECG Recordings'
        ordering = ['-timestamp']
        db_table = 'ecg_data'  # Tùy chỉnh tên bảng trong DB
        indexes = [
            models.Index(fields=['user', 'timestamp']),  # Index hóa các trường 'user' và 'timestamp'
        ]

class MedicalHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_history')
    condition = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.condition} - {self.user.username}"

    class Meta:
        verbose_name = 'Medical History'
        verbose_name_plural = 'Medical Histories'
        ordering = ['-date']
        db_table = 'medical_history'
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

class Medication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    class Meta:
        verbose_name = 'Medication'
        verbose_name_plural = 'Medications'
        ordering = ['-start_date']
        db_table = 'medication'
        indexes = [
            models.Index(fields=['user', 'start_date']),
        ]
