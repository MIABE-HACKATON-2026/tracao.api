from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from ..models.stores import Store, StoreMember, StoreAgent
from ..serializers.stores import (
    StoreSerializer, StoreMemberSerializer, StoreAgentSerializer
)

class StoreViewSet(viewsets.ModelViewSet):
    serializer_class = StoreSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Store.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class StoreMemberViewSet(viewsets.ModelViewSet):
    serializer_class = StoreMemberSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Filter members of stores managed by the current user
        return StoreMember.objects.filter(store__user=self.request.user)

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend_member(self, request, pk=None):
        member = self.get_object()
        member.status = 'suspended'
        member.save()
        return Response(StoreMemberSerializer(member).data)

class StoreAgentViewSet(viewsets.ModelViewSet):
    serializer_class = StoreAgentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return StoreAgent.objects.filter(store__user=self.request.user)
