from collections.abc import Mapping

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import serializers
from rest_framework.response import Response

from accounts.permissions import IsStaffOrAdmin
from accounts.views import SessionAPIView
from .availability import availability
from .models import Booking
from .serializers import BookingCreate, StrictIntegerField
from .services import BookingError
from .staff_services import staff_cancel, staff_create


class StaffCreate(BookingCreate):
    customer_id=StrictIntegerField(min_value=1,max_value=9223372036854775807)
    reason=serializers.CharField(max_length=500,allow_blank=False)


class CancelInput(serializers.Serializer):
    reason=serializers.CharField(max_length=500,allow_blank=False)

    def to_internal_value(self,data):
        if not isinstance(data,Mapping) or set(data)-{'reason'}:
            raise serializers.ValidationError({'non_field_errors':['Send only a reason field.']})
        return super().to_internal_value(data)


class SearchInput(serializers.Serializer):
    q=serializers.CharField(required=False,max_length=100,allow_blank=True)
    date=serializers.DateField(required=False)
    status=serializers.ChoiceField(choices=Booking.Status.values,required=False)
    page=StrictIntegerField(required=False,min_value=1,max_value=1000000,default=1)

    def to_internal_value(self,data):
        data=data.copy()
        for name in ['date','status']:
            if data.get(name)=='': data.pop(name)
        return super().to_internal_value(data)


def search_bookings(data):
    records=Booking.objects.select_related('customer','table').prefetch_related('overrides__actor').order_by('-start_at','-pk')
    if data.get('date'): records=records.filter(start_at__date=data['date'])
    if data.get('status'): records=records.filter(status=data['status'])
    q=data.get('q','').strip()
    if q:
        match=Q(customer__email__icontains=q)|Q(customer__first_name__icontains=q)|Q(customer__username__icontains=q)
        reference=q[3:] if q.upper().startswith('BK-') else q
        if reference.isdecimal() and len(reference)<19:
            match |= Q(pk=int(reference))|Q(table__table_number=int(reference))
        records=records.filter(match)
    return Paginator(records,25).get_page(data['page'])


def booking_data(b):
    return {'id':b.pk,'booking_id':f'BK-{b.pk}','customer_id':b.customer_id,'table_id':b.table_id,
            'start_at':b.start_at,'end_at':b.end_at,'party_size':b.party_size,'status':b.status}


class StaffBookingsView(SessionAPIView):
    permission_classes=[IsStaffOrAdmin]

    def get(self,request):
        query=SearchInput(data=request.query_params)
        query.is_valid(raise_exception=True)
        page=search_bookings(query.validated_data)
        return Response({'count':page.paginator.count,'page':page.number,'pages':page.paginator.num_pages,
                         'results':[booking_data(b) for b in page]})

    def post(self,request):
        data=StaffCreate(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            booking,created=staff_create(user=request.user,**data.validated_data)
        except BookingError as exc:
            details=exc.details
            if exc.code=='TABLE_UNAVAILABLE':
                details=availability(data.validated_data['start_at'],data.validated_data['party_size'])
            return Response({'code':exc.code,'message':exc.message,'details':details},status=exc.status)
        return Response(booking_data(booking),status=201 if created else 200)


class StaffCancelView(SessionAPIView):
    permission_classes=[IsStaffOrAdmin]

    def post(self,request,pk):
        data=CancelInput(data=request.data);data.is_valid(raise_exception=True)
        try:
            booking,changed=staff_cancel(user=request.user,booking_id=pk,**data.validated_data)
        except BookingError as exc:
            return Response({'code':exc.code,'message':exc.message},status=exc.status)
        return Response({**booking_data(booking),'changed':changed})


@method_decorator(ensure_csrf_cookie,name='dispatch')
class StaffBookingPage(SessionAPIView):
    permission_classes=[IsStaffOrAdmin]

    def get(self,request):
        query=SearchInput(data=request.query_params)
        query.is_valid(raise_exception=True)
        params=request.query_params.copy();params.pop('page',None)
        return render(request,'booking/staff.html',{'page':search_bookings(query.validated_data),
                                                   'query_string':params.urlencode()})
