from django.db import models
from django.db.models import Q


class MenuItem(models.Model):
    class Category(models.TextChoices):
        STARTERS = "Starters"
        MAIN_COURSE = "Main Course"
        DESSERTS = "Desserts"
        BEVERAGES = "Beverages"

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, max_length=2000)
    category = models.CharField(max_length=20, choices=Category)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=0), name="menu_nonnegative_price"),
            models.CheckConstraint(condition=~Q(name=""), name="menu_name_not_empty"),
            models.CheckConstraint(condition=Q(category__in=["Starters", "Main Course", "Desserts", "Beverages"]), name="menu_valid_category"),
        ]

    def __str__(self):
        return self.name
