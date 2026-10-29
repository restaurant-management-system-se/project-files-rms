from django.conf import settings
from django.db import models
from django.db.models import Q


class Order(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "Received"
        PREPARING = "Preparing"
        SERVED = "Served"
        CANCELLED = "Cancelled"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    booking = models.ForeignKey("booking.Booking", on_delete=models.PROTECT, null=True, blank=True, related_name="orders")
    status = models.CharField(max_length=10, choices=Status, default=Status.RECEIVED)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_mode = models.CharField(max_length=30, blank=True)
    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(total_amount__gte=0), name="order_nonnegative_total"),
            models.CheckConstraint(condition=Q(status__in=["Received", "Preparing", "Served", "Cancelled"]), name="order_valid_status"),
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey("menu.MenuItem", on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="orderitem_positive_quantity"),
            models.CheckConstraint(condition=Q(unit_price__gte=0), name="orderitem_nonnegative_price"),
        ]


class OrderRequestKey(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    key = models.UUIDField()
    payload = models.JSONField()
    order = models.OneToOneField(Order,on_delete=models.PROTECT)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['customer','key'],name='order_customer_retry_unique')]
