from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, ECGData, Device

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = ('id', 'username', 'email', 'birth_date', 'heart_disease_history', 'medications')
        read_only_fields = ('id',)

class ECGDataSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ECGData
        fields = ('id', 'username', 'timestamp', 'sample_rate', 'data')
        read_only_fields = ('id', 'username')

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'device_name', 'device_id', 'device_type', 'is_active', 'created_at', 'last_connected']
        read_only_fields = ['created_at', 'last_connected']

class ECGDataSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ECGData
        fields = ['timestamp', 'sample_rate', 'data']