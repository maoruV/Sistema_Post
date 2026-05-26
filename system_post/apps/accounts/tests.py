from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .forms import AdminPasswordResetForm

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin123', role='admin'
        )
        self.supervisor = User.objects.create_user(
            username='supervisor', password='super123', role='supervisor'
        )
        self.user = User.objects.create_user(
            username='usuario', password='user123', role='user'
        )

    def test_create_user_with_role(self):
        self.assertEqual(self.admin.role, 'admin')
        self.assertEqual(self.supervisor.role, 'supervisor')
        self.assertEqual(self.user.role, 'user')

    def test_is_admin(self):
        self.assertTrue(self.admin.is_admin())
        self.assertFalse(self.supervisor.is_admin())
        self.assertFalse(self.user.is_admin())

    def test_is_supervisor(self):
        self.assertTrue(self.admin.is_supervisor())
        self.assertTrue(self.supervisor.is_supervisor())
        self.assertFalse(self.user.is_supervisor())

    def test_can_update(self):
        self.assertTrue(self.admin.can_update())
        self.assertTrue(self.supervisor.can_update())
        self.assertFalse(self.user.can_update())

    def test_can_delete(self):
        self.assertTrue(self.admin.can_delete())
        self.assertTrue(self.supervisor.can_delete())
        self.assertFalse(self.user.can_delete())

    def test_can_create(self):
        self.assertTrue(self.admin.can_create())
        self.assertTrue(self.supervisor.can_create())
        self.assertTrue(self.user.can_create())

    def test_str(self):
        self.assertIn('admin', str(self.admin))
        self.assertIn('supervisor', str(self.supervisor))
        self.assertIn('usuario', str(self.user))


class LoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123', role='user'
        )

    def test_login_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'pass123',
        })
        self.assertRedirects(response, reverse('core:dashboard'))

    def test_login_failure(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'wrong',
        })
        self.assertRedirects(response, reverse('accounts:login'))

    def test_logout(self):
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))


class AdminPasswordResetFormTest(TestCase):
    def test_passwords_match(self):
        form = AdminPasswordResetForm(data={
            'password1': 'nueva123',
            'password2': 'nueva123',
        })
        self.assertTrue(form.is_valid())

    def test_passwords_mismatch(self):
        form = AdminPasswordResetForm(data={
            'password1': 'nueva123',
            'password2': 'otra123',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('coinciden', form.non_field_errors()[0])


class AdminPasswordResetViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin', password='admin123', email='admin@test.com'
        )
        self.admin.role = 'admin'
        self.admin.save()
        self.target_user = User.objects.create_user(
            username='target', password='oldpass', role='user'
        )

    def test_reset_password_by_admin(self):
        self.client.login(username='admin', password='admin123')
        url = reverse('accounts:password_reset_admin', args=[self.target_user.pk])
        response = self.client.post(url, {
            'password1': 'newpass123',
            'password2': 'newpass123',
        })
        self.assertRedirects(response, reverse('accounts:user_list'))
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password('newpass123'))

    def test_reset_password_requires_admin(self):
        self.client.login(username='target', password='oldpass')
        url = reverse('accounts:password_reset_admin', args=[self.target_user.pk])
        self.client.post(url, {
            'password1': 'hacked123',
            'password2': 'hacked123',
        })
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password('oldpass'))


class AdminAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin', password='admin123', role='admin'
        )
        self.normal_user = User.objects.create_user(
            username='user', password='user123', role='user'
        )

    def test_user_list_admin_access(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_list_user_blocked(self):
        self.client.login(username='user', password='user123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertNotEqual(response.status_code, 200)

    def test_user_create_admin_access(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('accounts:user_create'))
        self.assertEqual(response.status_code, 200)
