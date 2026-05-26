from django.test import TestCase
from .models import Supplier, SupplierInvoice


class SupplierModelTest(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(
            name='Distribuidora ABC',
            contact_person='Carlos López',
            email='abc@test.com',
            phone='555-0201',
        )

    def test_create_supplier(self):
        self.assertEqual(self.supplier.name, 'Distribuidora ABC')
        self.assertEqual(Supplier.objects.count(), 1)

    def test_str(self):
        self.assertEqual(str(self.supplier), 'Distribuidora ABC')


class SupplierInvoiceModelTest(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name='Proveedor Test')
        self.invoice = SupplierInvoice.objects.create(
            invoice_number='FAC-000001',
            supplier=self.supplier,
            total=500000,
            status='pendiente',
        )

    def test_create_invoice(self):
        self.assertEqual(self.invoice.invoice_number, 'FAC-000001')
        self.assertEqual(self.invoice.total, 500000)
        self.assertEqual(self.invoice.status, 'pendiente')

    def test_str(self):
        self.assertIn('FAC-000001', str(self.invoice))
        self.assertIn('Proveedor Test', str(self.invoice))

    def test_invoice_status_choices(self):
        self.invoice.status = 'pagada'
        self.invoice.save()
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'pagada')

    def test_supplier_relation(self):
        self.assertEqual(self.invoice.supplier.name, 'Proveedor Test')
