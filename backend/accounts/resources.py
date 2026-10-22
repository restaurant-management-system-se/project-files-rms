"""Read-only ownership boundaries; feature owners add business mutations separately."""
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from .permissions import IsOwnerOrStaffAdmin, owned_queryset
from .views import SessionAPIView


class OwnedResourceView(SessionAPIView):
    permission_classes = [IsOwnerOrStaffAdmin]
    model = None
    fields = ()

    def get(self, request, pk=None):
        queryset = self.model.objects.all().order_by("pk")
        if pk is not None:
            obj = get_object_or_404(queryset, pk=pk)
            self.check_object_permissions(request, obj)
            return Response(self.model.objects.filter(pk=obj.pk).values(*self.fields).get())
        return Response(list(owned_queryset(queryset, request.user).values(*self.fields)[:100]))
