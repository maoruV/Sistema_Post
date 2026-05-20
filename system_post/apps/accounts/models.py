from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        SUPERVISOR = 'supervisor', 'Supervisor'
        USER = 'user', 'Usuario'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        verbose_name='Rol'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_supervisor(self):
        return self.role in [self.Role.ADMIN, self.Role.SUPERVISOR] or self.is_superuser

    def can_create(self):
        return True

    def can_update(self):
        return self.role in [self.Role.ADMIN, self.Role.SUPERVISOR] or self.is_superuser

    def can_delete(self):
        return self.role in [self.Role.ADMIN, self.Role.SUPERVISOR] or self.is_superuser
