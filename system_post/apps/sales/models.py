from django.db import models
from django.conf import settings
from apps.inventory.models import Product
from apps.clients.models import Client


class Sale(models.Model):
    invoice_number = models.CharField(max_length=20, unique=True, verbose_name='Folio')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales', verbose_name='Cliente')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sales', verbose_name='Vendedor')
    date = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Fecha')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Subtotal')
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='IVA')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total')
    class Status(models.TextChoices):
        PENDING = 'pendiente', 'Pendiente'
        PAID = 'pagada', 'Pagada'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PAID, db_index=True, verbose_name='Estado')

    class PaymentMethod(models.TextChoices):
        CASH = 'efectivo', 'Efectivo'
        CARD = 'tarjeta', 'Tarjeta'
        TRANSFER = 'transferencia', 'Transferencia'
        PENDING = 'pendiente', 'Pendiente'

    payment_method = models.CharField(max_length=50, choices=PaymentMethod.choices, default=PaymentMethod.CASH, verbose_name='Método de pago')
    amount_received = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Monto recibido')
    change = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Cambio')
    is_active = models.BooleanField(default=True, db_index=True, verbose_name='Activa')

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['is_active', 'status', '-date'], name='idx_sale_active_status_date'),
        ]

    def __str__(self):
        return f'Venta {self.invoice_number} - ${self.total}'


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items', verbose_name='Venta')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name='Producto')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Cantidad')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio unitario')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Subtotal')

    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Ventas'
        ordering = ['id']

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
