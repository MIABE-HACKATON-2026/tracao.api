from rest_framework import serializers
from ..models.system import SyncQueue, Notification, TraceabilityLog, QRCode, FraudAlert, BlockchainRecord

class SyncQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncQueue
        fields = (
            'id', 'agent', 'action_type', 'payload', 'local_id', 
            'status', 'conflict_reason', 'created_locally_at', 'synced_at', 'created_at'
        )
        read_only_fields = ('id', 'agent', 'status', 'conflict_reason', 'synced_at', 'created_at')

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'user', 'type', 'message', 'read', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

class TraceabilityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TraceabilityLog
        fields = ('id', 'batch', 'action_type', 'performed_by', 'metadata', 'created_at')
        read_only_fields = ('id', 'created_at')

class QRCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRCode
        fields = ('id', 'batch', 'qr_data', 'created_at')
        read_only_fields = ('id', 'created_at')

class FraudAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = FraudAlert
        fields = (
            'id', 'user', 'batch', 'parcel', 'type', 
            'score', 'status', 'resolution_comment', 'resolved_by', 'resolved_at', 'created_at'
        )
        read_only_fields = ('id', 'created_at', 'resolved_by', 'resolved_at')

class BlockchainRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockchainRecord
        fields = (
            'id', 'entity_type', 'entity_id', 'hash', 
            'tx_hash', 'chain', 'block_number', 'anchored_at', 'created_at'
        )
        read_only_fields = ('id', 'created_at')