from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from ..models.batches import Transaction, Batch
from ..serializers.commerce import TransactionSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(buyer=user) | Transaction.objects.filter(seller=user)

    def perform_create(self, serializer):
        batch = serializer.validated_data['batch']
        # Prevent double sale
        if Transaction.objects.filter(batch=batch, status='completed').exists():
            raise serializers.ValidationError("This batch has already been sold.")
        
        serializer.save(seller=batch.farmer, status='pending')

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_transaction(self, request, pk=None):
        tx = self.get_object()
        if tx.status != 'pending':
            return Response({"error": "Transaction is not pending"}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            tx.status = 'completed'
            tx.save()
            
            # Close the batch
            batch = tx.batch
            batch.status = 'closed'
            batch.save()
            
        return Response(TransactionSerializer(tx).data)
