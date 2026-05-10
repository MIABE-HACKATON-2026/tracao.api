from rest_framework import serializers
from ..models.batches import Transaction
from .auth import UserSerializer
from .production import BatchSerializer

class TransactionSerializer(serializers.ModelSerializer):
    buyer_details = UserSerializer(source='buyer', read_only=True)
    seller_details = UserSerializer(source='seller', read_only=True)
    batch_details = BatchSerializer(source='batch', read_only=True)

    class Meta:
        model = Transaction
        fields = (
            'id', 'batch', 'batch_details', 'buyer', 'buyer_details', 
            'seller', 'seller_details', 'quantity', 'price', 
            'status', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'seller', 'status', 'created_at', 'updated_at')
