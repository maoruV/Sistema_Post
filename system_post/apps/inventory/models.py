from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    name = models.CharField(max_length=200, db_index=True, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name='Categoría')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio')
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Costo')
    stock = models.PositiveIntegerField(default=0, db_index=True, verbose_name='Stock')
    min_stock = models.PositiveIntegerField(default=0, verbose_name='Stock mínimo')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Imagen')
    is_active = models.BooleanField(default=True, db_index=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (SKU: {self.sku})'

    @property
    def is_low_stock(self):
        return self.stock <= self.min_stock
