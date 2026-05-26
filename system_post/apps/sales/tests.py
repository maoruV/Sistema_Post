import json
from django.test import TestCase, Client as TestClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.inventory.models import Product, Category
from apps.clients.models import Client as ClientModel
from .models import Sale, SaleItem
from .utils import InvoiceCounter, next_invoice_number

User = get_user_model()


class InvoiceCounterTest(TestCase):
    def test_next_invoice_number(self):
        num1 = next_invoice_number('VNT')
        self.assertEqual(num1, 'VNT-000001')
        num2 = next_invoice_number('VNT')
        self.assertEqual(num2, 'VNT-000002')

    def test_prefix_isolation(self):
        vnt = next_invoice_number('VNT')
        fac = next_invoice_number('FAC')
        self.assertEqual(vnt, 'VNT-000001')
        self.assertEqual(fac, 'FAC-000001')


class SaleModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='vendedor', password='pass', role='user'
        )
        self.client_obj = ClientModel.objects.create(name='Cliente Test')

    def test_create_sale(self):
        sale = Sale.objects.create(
            invoice_number='VNT-000001',
            user=self.user,
            subtotal=100000,
            tax=19000,
            total=119000,
            status='pagada',
        )
        self.assertEqual(sale.invoice_number, 'VNT-000001')
        self.assertEqual(sale.subtotal, 100000)
        self.assertEqual(sale.tax, 19000)
        self.assertEqual(sale.total, 119000)
        self.assertTrue(sale.is_active)

    def test_sale_default_status(self):
        sale = Sale.objects.create(
            invoice_number='VNT-000002',
            user=self.user,
            subtotal=0,
            total=0,
        )
        self.assertEqual(sale.status, 'pagada')

    def test_sale_str(self):
        sale = Sale.objects.create(
            invoice_number='VNT-000003',
            user=self.user,
            subtotal=50000,
            total=50000,
        )
        self.assertIn('VNT-000003', str(sale))


class SaleIVATest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='vendedor', password='pass', role='user'
        )
        self.category = Category.objects.create(name='Test')
        self.product = Product.objects.create(
            sku='TST-001', name='Producto Test',
            price=100000, stock=10, category=self.category,
        )
    def _create_sale(self, apply_iva):
        invoice_number = next_invoice_number('VNT')
        sale = Sale.objects.create(
            invoice_number=invoice_number,
            user=self.user,
            subtotal=100000,
            tax=100000 * 0.19 if apply_iva else 0,
            total=100000 + (100000 * 0.19 if apply_iva else 0),
        )
        return sale

    def test_iva_calculation(self):
        sale = self._create_sale(apply_iva=True)
        self.assertEqual(sale.tax, 19000)
        self.assertEqual(sale.total, 119000)

    def test_no_iva(self):
        sale = self._create_sale(apply_iva=False)
        self.assertEqual(sale.tax, 0)
        self.assertEqual(sale.total, 100000)


class SaleFlowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='vendedor', password='pass', role='user'
        )
        self.category = Category.objects.create(name='Test')
        self.product = Product.objects.create(
            sku='TST-001', name='Laptop Test',
            price=500000, stock=5, category=self.category,
        )

    def test_complete_sale_flow(self):
        self.client.login(username='vendedor', password='pass')
        sale_data = json.dumps({
            'items': [{
                'product_id': self.product.id,
                'quantity': 2,
                'unit_price': 500000,
            }],
            'apply_iva': True,
            'payment_method': 'efectivo',
            'amount_received': 1200000,
        })
        response = self.client.post(
            reverse('sales:sale_complete'),
            {'sale_data': sale_data},
        )
        self.assertEqual(response.status_code, 302)
        sale = Sale.objects.latest('id')
        self.assertEqual(sale.subtotal, 1000000)
        self.assertEqual(sale.tax, 190000)
        self.assertEqual(sale.total, 1190000)

    def test_stock_deduction_on_sale(self):
        self.client.login(username='vendedor', password='pass')
        sale_data = json.dumps({
            'items': [{
                'product_id': self.product.id,
                'quantity': 3,
                'unit_price': 500000,
            }],
            'apply_iva': False,
            'payment_method': 'efectivo',
            'amount_received': 1500000,
        })
        self.client.post(
            reverse('sales:sale_complete'),
            {'sale_data': sale_data},
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)

    def test_insufficient_stock(self):
        self.client.login(username='vendedor', password='pass')
        response = self.client.post(
            reverse('sales:add_item'),
            data=json.dumps({
                'product_id': self.product.id,
                'quantity': 10,
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Stock insuficiente', response.json()['error'])

    def test_sale_cancel_restores_stock(self):
        self.client.login(username='vendedor', password='pass')
        sale_data = json.dumps({
            'items': [{
                'product_id': self.product.id,
                'quantity': 2,
                'unit_price': 500000,
            }],
            'apply_iva': False,
            'payment_method': 'efectivo',
        })
        self.client.post(
            reverse('sales:sale_complete'),
            {'sale_data': sale_data},
        )
        sale = Sale.objects.latest('id')
        admin = User.objects.create_superuser(
            username='admin', password='admin123', role='admin'
        )
        admin_client = TestClient()
        admin_client.login(username='admin', password='admin123')
        admin_client.post(reverse('sales:sale_cancel', args=[sale.pk]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)


class SaleAccessTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', password='admin123', role='admin'
        )
        self.user = User.objects.create_user(
            username='user', password='user123', role='user'
        )

    def test_sale_list_authenticated(self):
        self.client.login(username='user', password='user123')
        response = self.client.get(reverse('sales:sale_list'))
        self.assertEqual(response.status_code, 200)

    def test_sale_new_authenticated(self):
        self.client.login(username='user', password='user123')
        response = self.client.get(reverse('sales:sale_new'))
        self.assertEqual(response.status_code, 200)

    def test_sale_list_unauthenticated_redirect(self):
        response = self.client.get(reverse('sales:sale_list'))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('sales:sale_list')}"
        )
