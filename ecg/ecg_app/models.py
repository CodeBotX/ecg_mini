from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField  # Nếu dùng Django 3.1+ và không dùng PostgreSQL

# Hồ sơ người dùng, chứa thông tin bệnh lý
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birth_date = models.DateField(null=True, blank=True)
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
