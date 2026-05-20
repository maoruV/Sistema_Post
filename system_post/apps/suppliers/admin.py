from django.contrib import admin
from .models import Supplier, SupplierInvoice


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone']
    search_fields = ['name', 'email', 'nit']


@admin.register(SupplierInvoice)
class SupplierInvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'supplier', 'date', 'total', 'status']
    list_filter = ['status', 'date']
