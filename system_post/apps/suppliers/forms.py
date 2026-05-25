from django import forms
from .models import Supplier, SupplierInvoice
from .utils import next_supplier_invoice_number


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'email', 'phone', 'address', 'nit']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input'})


class SupplierInvoiceForm(forms.ModelForm):
    class Meta:
        model = SupplierInvoice
        fields = ['supplier', 'total', 'status', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input'})

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.invoice_number:
            instance.invoice_number = next_supplier_invoice_number()
        if commit:
            instance.save()
        return instance
