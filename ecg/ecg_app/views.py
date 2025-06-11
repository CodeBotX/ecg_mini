from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Profile, ECGData, Device, MedicalHistory, Medication
from .serializers import ECGDataSerializer, DeviceSerializer
import os
import json
from rest_framework.views import APIView
from django.utils.dateparse import parse_datetime
from django.utils import timezone



# --- API ViewSets ---
    
class RecordingToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]  # người dùng web phải đăng nhập

    def post(self, request, device_id):
        try:
            device = Device.objects.get(device_id=device_id, user=request.user)
        except Device.DoesNotExist:
            return Response({"detail": "No device"}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get("action")
        if action == "start":
            device.recording = True
        elif action == "stop":
            device.recording = False
        else:
            return Response({"detail": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        device.save(update_fields=["recording"])
        return Response({"recording": device.recording})
    
@login_required
def monitor_list_view(request):
    devices = Device.objects.filter(user=request.user)
    return render(request, 'ecg_app/monitor_list.html', {'devices': devices})

@login_required
def monitor_view(request, device_id):
    device = get_object_or_404(Device, device_id=device_id, user=request.user)
    return render(request, "ecg_app/monitor.html", {"device": device})

# @login_required
# def monitor_view(request):
#     return render(request, 'ecg_app/monitor.html')


#-----------------------------------------------------------------------------

# --- Auth Views ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('ecg_app:home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin')
            return render(request, 'ecg_app/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'ecg_app:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng')
            return render(request, 'ecg_app/login.html')

    return render(request, 'ecg_app/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Validation
        if not username or not email or not password or not password2:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin')
            return render(request, 'ecg_app/register.html')

        if password != password2:
            messages.error(request, 'Mật khẩu xác nhận không khớp')
            return render(request, 'ecg_app/register.html')

        if len(password) < 8:
            messages.error(request, 'Mật khẩu phải có ít nhất 8 ký tự')
            return render(request, 'ecg_app/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Tên đăng nhập đã tồn tại')
            return render(request, 'ecg_app/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email đã được sử dụng')
            return render(request, 'ecg_app/register.html')

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user)
            messages.success(request, 'Đăng ký thành công. Vui lòng đăng nhập.')
            return redirect('ecg_app:login')
        except Exception as e:
            messages.error(request, f'Lỗi khi đăng ký: {str(e)}')
            return render(request, 'ecg_app/register.html')

    return render(request, 'ecg_app/register.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Đăng xuất thành công')
    return redirect('ecg_app:login')

# --- Main Views ---
@login_required
def home_view(request):
    devices = Device.objects.filter(user=request.user)
    recent_measurements = ECGData.objects.filter(user=request.user).order_by('-timestamp')[:5]
    return render(request, 'ecg_app/home.html', {
        'devices': devices,
        'recent_measurements': recent_measurements
    })

@login_required
def device_management_view(request):
    devices = Device.objects.filter(user=request.user)
    return render(request, 'ecg_app/devices.html', {'devices': devices})

@login_required
def measurement_history_view(request):
    measurements = ECGData.objects.filter(user=request.user).order_by('-timestamp')
    devices = Device.objects.filter(user=request.user)
    return render(request, 'ecg_app/history.html', {
        'measurements': measurements,
        'devices': devices
    })

# --- Profile Views ---
@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'ecg_app/profile.html', {'profile': profile})

@login_required
def medical_history_view(request):
    history = MedicalHistory.objects.filter(user=request.user)
    return render(request, 'ecg_app/medical_history.html', {'medical_history': history})

@login_required
def medication_view(request):
    meds = Medication.objects.filter(user=request.user)
    return render(request, 'ecg_app/medications.html', {'medications': meds})

# --- Profile Image Management ---
@login_required
def upload_profile_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        profile = get_object_or_404(Profile, user=request.user)
        if profile.image and os.path.isfile(profile.image.path):
            os.remove(profile.image.path)
        profile.image = request.FILES['image']
        profile.save()
        messages.success(request, 'Cập nhật ảnh đại diện thành công')
    return redirect('profile')

@login_required
def remove_profile_image(request):
    if request.method == 'POST':
        profile = get_object_or_404(Profile, user=request.user)
        if profile.image and os.path.isfile(profile.image.path):
            os.remove(profile.image.path)
        profile.image = None
        profile.save()
        messages.success(request, 'Xóa ảnh đại diện thành công')
    return redirect('profile')

# --- Device Management ---
@login_required
def add_device(request):
    if request.method == 'POST':
        device_name = request.POST.get('device_name')
        device_id = request.POST.get('device_id')
        device_type = request.POST.get('device_type')
        
        if not device_name or not device_id or not device_type:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin')
            return redirect('ecg_app:device_management')
            
        try:
            Device.objects.create(
                user=request.user,
                device_name=device_name,
                device_id=device_id,
                device_type=device_type
            )
            messages.success(request, 'Đã thêm thiết bị thành công')
        except Exception as e:
            messages.error(request, f'Lỗi khi thêm thiết bị: {str(e)}')
            
    return redirect('ecg_app:device_management')

@login_required
def edit_device(request):
    if request.method == 'POST':
        try:
            device = Device.objects.get(id=request.POST.get('device_id'), user=request.user)
            device.device_name = request.POST.get('device_name')
            device.device_type = request.POST.get('device_type')
            device.save()
            messages.success(request, 'Cập nhật thiết bị thành công.')
        except Device.DoesNotExist:
            messages.error(request, 'Không tìm thấy thiết bị.')
        except Exception as e:
            messages.error(request, f'Lỗi khi cập nhật thiết bị: {e}')
    return redirect('device_management')

@login_required
def delete_device(request):
    if request.method == 'POST':
        try:
            device = Device.objects.get(id=request.POST.get('device_id'), user=request.user)
            device.delete()
            messages.success(request, 'Thiết bị đã được xóa.')
        except Device.DoesNotExist:
            messages.error(request, 'Không tìm thấy thiết bị.')
        except Exception as e:
            messages.error(request, f'Lỗi khi xóa thiết bị: {e}')
    return redirect('device_management')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def latest_measurement(request):
    try:
        latest = ECGData.objects.filter(user=request.user).latest('timestamp')
        serializer = ECGDataSerializer(latest)
        return Response(serializer.data)
    except ECGData.DoesNotExist:
        return Response({'error': 'No measurements found'}, status=status.HTTP_404_NOT_FOUND)

@login_required
def delete_measurement(request):
    if request.method == 'POST':
        measurement_id = request.POST.get('measurement_id')
        try:
            measurement = ECGData.objects.get(id=measurement_id, user=request.user)
            measurement.delete()
            messages.success(request, 'Đã xóa đo thành công')
        except ECGData.DoesNotExist:
            messages.error(request, 'Không tìm thấy đo')
    return redirect('ecg_app:history')

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        # Get the user's profile
        profile = request.user.profile
        
        # Update user information
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()
        
        # Update profile information
        profile.blood_type = request.POST.get('blood_type', '')
        profile.height = request.POST.get('height', None)
        profile.weight = request.POST.get('weight', None)
        profile.save()
        
        messages.success(request, 'Thông tin cá nhân đã được cập nhật thành công.')
        return redirect('ecg_app:profile')
    
    return redirect('ecg_app:profile')

@login_required
def add_medical_history(request):
    if request.method == 'POST':
        condition = request.POST.get('condition')
        date = request.POST.get('date')
        description = request.POST.get('description')
        
        if condition and date:
            MedicalHistory.objects.create(
                user=request.user,
                condition=condition,
                date=date,
                description=description
            )
            messages.success(request, 'Đã thêm bệnh án mới thành công.')
        else:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin bệnh án.')
    
    return redirect('ecg_app:profile')

@login_required
def edit_medical_history(request, history_id):
    try:
        history = MedicalHistory.objects.get(id=history_id, user=request.user)
        if request.method == 'POST':
            history.condition = request.POST.get('condition')
            history.date = request.POST.get('date')
            history.description = request.POST.get('description')
            history.save()
            messages.success(request, 'Đã cập nhật bệnh án thành công.')
    except MedicalHistory.DoesNotExist:
        messages.error(request, 'Không tìm thấy bệnh án.')
    
    return redirect('ecg_app:profile')

@login_required
def delete_medical_history(request, history_id):
    try:
        history = MedicalHistory.objects.get(id=history_id, user=request.user)
        history.delete()
        messages.success(request, 'Đã xóa bệnh án thành công.')
    except MedicalHistory.DoesNotExist:
        messages.error(request, 'Không tìm thấy bệnh án.')
    
    return redirect('ecg_app:profile')

@login_required
def add_medication(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        dosage = request.POST.get('dosage')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if name and dosage and start_date:
            Medication.objects.create(
                user=request.user,
                name=name,
                dosage=dosage,
                start_date=start_date,
                end_date=end_date
            )
            messages.success(request, 'Đã thêm thuốc mới thành công.')
        else:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin thuốc.')
    
    return redirect('ecg_app:profile')

@login_required
def edit_medication(request, medication_id):
    try:
        medication = Medication.objects.get(id=medication_id, user=request.user)
        if request.method == 'POST':
            medication.name = request.POST.get('name')
            medication.dosage = request.POST.get('dosage')
            medication.start_date = request.POST.get('start_date')
            medication.end_date = request.POST.get('end_date')
            medication.save()
            messages.success(request, 'Đã cập nhật thông tin thuốc thành công.')
    except Medication.DoesNotExist:
        messages.error(request, 'Không tìm thấy thông tin thuốc.')
    
    return redirect('ecg_app:profile')

@login_required
def delete_medication(request, medication_id):
    try:
        medication = Medication.objects.get(id=medication_id, user=request.user)
        medication.delete()
        messages.success(request, 'Đã xóa thông tin thuốc thành công.')
    except Medication.DoesNotExist:
        messages.error(request, 'Không tìm thấy thông tin thuốc.')
    
    return redirect('ecg_app:profile')