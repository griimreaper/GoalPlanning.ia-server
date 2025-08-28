# models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import string, secrets

class UserManager(BaseUserManager):
    def make_random_password(self, length=12):
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(chars) for _ in range(length))


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()  # <-- usamos el manager personalizado

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    # Evita conflictos con auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_users',  # <--- cambio de nombre
        blank=True,
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  # <--- cambio de nombre
        blank=True,
        help_text='Specific permissions for this user.'
    )

    def __str__(self):
        return self.email
