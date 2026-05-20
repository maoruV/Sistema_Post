from django.db import models


class Supplier(models.Model):
    name = models.CharField(max_length=200, db_index=True, verbose_name='Nombre')
    contact_person = models.CharField(max_length=200, blank=True, verbose_name='Persona de contacto')
    email = models.EmailField(blank=True, verbose_name='Email')
    phone = models.CharField(max_length=20, db_index=True, blank=True, verbose_name='Teléfono')
    address = models.CharField(max_length=500, blank=True, verbose_name='Dirección')
    nit = models.CharField(max_length=13, blank=True, verbose_name='NIT')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['name']

    def __str__(self):
        return self.name


class SupplierInvoice(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pendiente', 'Pendiente'
        PAID = 'pagada', 'Pagada'
        CANCELLED = 'cancelada', 'Cancelada'

    invoice_number = models.CharField(max_length=20, unique=True, verbose_name='Folio')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='invoices', verbose_name='Proveedor')
    date = models.DateField(auto_now_add=True, verbose_name='Fecha')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name='Estado')
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Factura de Proveedor'
        verbose_name_plural = 'Facturas de Proveedores'
        ordering = ['-date']

    def __str__(self):
        return f'Factura {self.invoice_number} - {self.supplier.name}'
