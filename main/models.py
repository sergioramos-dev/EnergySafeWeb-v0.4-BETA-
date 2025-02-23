from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string

class CustomUser(AbstractUser):
    def generate_id():
        return get_random_string(24, allowed_chars='abcdef0123456789')
    
    id = models.CharField(
        primary_key=True,
        max_length=24,
        default=generate_id,
        editable=False
    )
    email = models.EmailField(unique=True)
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_groups_related",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions_related",
        blank=True
    )

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email
