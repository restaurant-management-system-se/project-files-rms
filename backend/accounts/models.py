from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class UserManager(DjangoUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        # Public registration must use this method and must not accept role flags.
        if (extra_fields.get("role", "Customer") != "Customer"
                or extra_fields.get("is_staff") or extra_fields.get("is_superuser")):
            raise ValueError("Privileged users must be provisioned by an administrator.")
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields["role"] = "Admin"
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "Customer"
        STAFF = "Staff"
        ADMIN = "Admin"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=8, choices=Role, default=Role.CUSTOMER)
    objects = UserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="user_email_case_unique"),
            models.CheckConstraint(condition=~Q(email=""), name="user_email_not_empty"),
            models.CheckConstraint(condition=Q(role__in=["Customer", "Staff", "Admin"]), name="user_valid_role"),
            models.CheckConstraint(condition=Q(is_staff=False) | Q(role="Admin"), name="user_admin_staff_flag"),
            models.CheckConstraint(condition=Q(is_superuser=False) | Q(role="Admin"), name="user_admin_superuser_flag"),
        ]

    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email).lower()
        self.phone = self.phone or None
        # Restaurant staff use the later staff dashboard, not Django Admin.
        self.is_staff = self.role == self.Role.ADMIN
        if self.role != self.Role.ADMIN:
            self.is_superuser = False
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"email", "phone", "is_staff", "is_superuser"}
        super().save(*args, **kwargs)
