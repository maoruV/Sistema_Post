from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'unit_price', 'subtotal']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    inlines = [SaleItemInline]
    list_display = ['invoice_number', 'date', 'client', 'user', 'total', 'status', 'is_active']
    list_filter = ['date', 'status', 'is_active']
