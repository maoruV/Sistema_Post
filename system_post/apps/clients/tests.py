from django.test import TestCase
from .models import Client


class ClientModelTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            name='Juan Pérez',
            email='juan@test.com',
            phone='555-0101',
            address='Calle 123',
            cc='1234567890',
        )

    def test_create_client(self):
        self.assertEqual(self.client.name, 'Juan Pérez')
        self.assertEqual(Client.objects.count(), 1)

    def test_str(self):
        self.assertEqual(str(self.client), 'Juan Pérez')

    def test_optional_fields(self):
        client = Client.objects.create(name='Test')
        self.assertEqual(client.email, '')
        self.assertEqual(client.phone, '')
        self.assertEqual(client.address, '')
        self.assertEqual(client.cc, '')
