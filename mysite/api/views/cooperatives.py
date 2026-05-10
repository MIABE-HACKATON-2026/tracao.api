from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from ..models.cooperatives import Cooperative, CoopMember, CoopAgent
from ..serializers.cooperatives import (
    CooperativeSerializer, CoopMemberSerializer, CoopAgentSerializer
)

class CooperativeViewSet(viewsets.ModelViewSet):
    serializer_class = CooperativeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Cooperative.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CoopMemberViewSet(viewsets.ModelViewSet):
    serializer_class = CoopMemberSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Filter members of cooperatives managed by the current user
        return CoopMember.objects.filter(cooperative__user=self.request.user)

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend_member(self, request, pk=None):
        member = self.get_object()
        member.status = 'suspended'
        member.save()
        return Response(CoopMemberSerializer(member).data)

class CoopAgentViewSet(viewsets.ModelViewSet):
    serializer_class = CoopAgentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return CoopAgent.objects.filter(cooperative__user=self.request.user)
