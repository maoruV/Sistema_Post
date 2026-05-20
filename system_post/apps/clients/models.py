from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=200, db_index=True, verbose_name='Nombre')
    email = models.EmailField(blank=True, verbose_name='Email')
    phone = models.CharField(max_length=20, db_index=True, blank=True, verbose_name='Teléfono')
    address = models.CharField(max_length=500, blank=True, verbose_name='Dirección')
    cc = models.CharField(max_length=13, blank=True, verbose_name='CC')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']

    def __str__(self):
        return self.name
