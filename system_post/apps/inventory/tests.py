from django.test import TestCase
from .models import Category, Product


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Electrónicos',
            description='Productos electrónicos'
        )

    def test_create_category(self):
        self.assertEqual(self.category.name, 'Electrónicos')
        self.assertEqual(Category.objects.count(), 1)

    def test_str(self):
        self.assertEqual(str(self.category), 'Electrónicos')

    def test_ordering(self):
        Category.objects.create(name='Alimentos')
        categories = Category.objects.all()
        self.assertEqual(categories[0].name, 'Alimentos')


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Ropa')
        self.product = Product.objects.create(
            sku='ROP-001',
            name='Camisa',
            price=60000,
            stock=20,
            min_stock=5,
            category=self.category,
        )

    def test_create_product(self):
        self.assertEqual(self.product.sku, 'ROP-001')
        self.assertEqual(self.product.price, 60000)
        self.assertEqual(self.product.stock, 20)

    def test_is_low_stock(self):
        self.assertFalse(self.product.is_low_stock)
        self.product.stock = 3
        self.assertTrue(self.product.is_low_stock)

    def test_stock_boundary(self):
        self.product.stock = 5
        self.assertTrue(self.product.is_low_stock)

    def test_str(self):
        self.assertIn('Camisa', str(self.product))
        self.assertIn('ROP-001', str(self.product))

    def test_default_is_active(self):
        self.assertTrue(self.product.is_active)

    def test_category_relation(self):
        self.assertEqual(self.product.category.name, 'Ropa')
