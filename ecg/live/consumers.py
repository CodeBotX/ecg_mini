# live/consumers.py
import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from devices.models import Device
from ecg.models import ECGData
class ECGUploadConsumer(AsyncWebsocketConsumer):
    """
    ESP32 → ws://HOST/ws/device/<device_id>/upload/
    Gói JSON:
    {
        "timestamp": "2025-06-11T12:34:56Z",
        "ecg_data": [....]          // list int/float
    }
    """
    async def connect(self):
        self.device_id = self.scope["url_route"]["kwargs"]["device_id"]
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        ecg_data  = data.get("ecg_data")
        ts_string = data.get("timestamp")

        if not ecg_data or ts_string is None:
            return

        # tra thiết bị
        try:
            device = await database_sync_to_async(Device.objects.select_related("user").get)(device_id=self.device_id)
        except Device.DoesNotExist:
            await self.send(json.dumps({"error": "unknown device"}))
            return

        # phát realtime cho browser
        await self.channel_layer.group_send(
            f"device_{self.device_id}",
            {"type": "ecg_data", "payload": ecg_data}
        )

        # lưu nếu đang ghi
        if device.recording:
            ts = parse_datetime(ts_string) or timezone.now()
            await database_sync_to_async(ECGData.objects.create)(
                user=device.user, timestamp=ts, sample_rate=len(ecg_data), data=ecg_data
            )

        device.last_connected = timezone.now()
        await database_sync_to_async(device.save)(update_fields=["last_connected"])
        await self.send(json.dumps({"stored": device.recording}))


class ECGMonitorConsumer(AsyncWebsocketConsumer):
    """
    Browser → ws://HOST/ws/monitor/<device_id>/
    Chỉ listen, không gửi.
    """
    async def connect(self):
        self.device_id  = self.scope["url_route"]["kwargs"]["device_id"]
        self.group_name = f"device_{self.device_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def ecg_data(self, event):
        await self.send(json.dumps(event["payload"]))
