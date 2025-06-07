from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Profile, ECGData
from .serializers import UserSerializer, ProfileSerializer, ECGDataSerializer
from rest_framework.permissions import IsAuthenticated
from .signals_filters import LowPassFilter, HighPassFilter, BandPassFilter
from .transforms import DiscreteFourierTransform, InverseDiscreteFourierTransform, ZTransform

# API ViewSet cho ECGData
class ECGDataViewSet(viewsets.ModelViewSet):
    queryset = ECGData.objects.all()
    serializer_class = ECGDataSerializer
    permission_classes = [IsAuthenticated]  # Chỉ cho phép người dùng đã đăng nhập

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # Lưu ECGData gắn với người dùng hiện tại

    def create(self, request, *args, **kwargs):
        """
        Override method create() để gửi dữ liệu JSON array vào API.
        """
        data = request.data.copy()
        data['user'] = request.user.id  # gắn user vào
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# API ViewSet cho Profile của người dùng
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]  # Chỉ cho phép người dùng đã đăng nhập

    def get_queryset(self):
        """
        Lấy Profile của người dùng hiện tại.
        """
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Tạo Profile cho người dùng nếu chưa có.
        """
        serializer.save(user=self.request.user)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Validate password
                validate_password(serializer.validated_data['password'])
                
                # Create user
                user = serializer.save()
                
                # Create profile
                Profile.objects.create(user=user)
                
                return Response({
                    "message": "User created successfully",
                    "user": serializer.data
                }, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({
                    "error": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ECGDataFilterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """ Xử lý GET request với bộ lọc """

        filter_type = request.GET.get('filter_type', None)
        cutoff_freq = request.GET.get('cutoff_freq', 40)  # Tần số cắt mặc định là 40 Hz
        low_cut = request.GET.get('low_cut', 0)
        high_cut = request.GET.get('high_cut', 50)

        # Lấy tất cả dữ liệu ECG của người dùng
        ecg_data_queryset = self.get_user_ecg_data(request.user)

        # Nếu yêu cầu lọc dữ liệu, thực hiện lọc
        if filter_type:
            try:
                filtered_data = self.apply_filter(
                    ecg_data_queryset,
                    filter_type,
                    float(cutoff_freq),
                    float(low_cut),
                    float(high_cut)
                )
                return self.respond_with_filtered_data(filtered_data)

            except ValueError:
                return Response({"error": "Invalid filter parameters"}, status=status.HTTP_400_BAD_REQUEST)

        # Nếu không có bộ lọc yêu cầu, trả về dữ liệu chưa lọc
        return self.respond_with_filtered_data(ecg_data_queryset)

    def get_user_ecg_data(self, user):
        """ Lấy tất cả dữ liệu ECG của người dùng """
        return ECGData.objects.filter(user=user)

    def apply_filter(self, ecg_data_queryset, filter_type, cutoff_freq, low_cut, high_cut):
        """ Áp dụng bộ lọc tương ứng lên dữ liệu ECG """
        filter = self.get_filter_by_type(filter_type, cutoff_freq, low_cut, high_cut)
        
        # Lọc dữ liệu ECG
        filtered_data = []
        for ecg in ecg_data_queryset:
            filtered_signal = filter.apply(ecg.data)  # Lọc tín hiệu ECG
            ecg.data = filtered_signal  # Cập nhật dữ liệu ECG đã lọc
            filtered_data.append(ecg)

        return filtered_data

    def get_filter_by_type(self, filter_type, cutoff_freq, low_cut, high_cut):
        """ Trả về bộ lọc tương ứng với loại được yêu cầu """
        if filter_type == 'lowpass':
            return LowPassFilter(cutoff_freq, 250)  # Giả sử sample_rate là 250
        elif filter_type == 'highpass':
            return HighPassFilter(cutoff_freq, 250)
        elif filter_type == 'bandpass':
            return BandPassFilter(low_cut, high_cut, 250)
        else:
            raise ValueError("Invalid filter type")

    def respond_with_filtered_data(self, ecg_data_queryset):
        """ Trả về dữ liệu ECG (đã lọc hoặc chưa lọc) """
        serializer = ECGDataSerializer(ecg_data_queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)