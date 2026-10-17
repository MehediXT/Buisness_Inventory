from django.test import TestCase
from accounts.models import Company, User
from rest_framework.test import APIClient
from rest_framework import status


class AccountsTests(TestCase):
    def setUp(self):
        self.company1 = Company.objects.create(name="Company 1")
        self.company2 = Company.objects.create(name="Company 2")

        self.admin = User.objects.create_user(
            username="admin", password="password123", role="admin"
        )
        self.manager = User.objects.create_user(
            username="manager", password="password123", company=self.company1, role="manager"
        )
        self.staff = User.objects.create_user(
            username="staff", password="password123", company=self.company1, role="staff"
        )

    def test_manager_cannot_delete_or_edit_foreign_company(self):
        client = APIClient()
        client.force_authenticate(user=self.manager)

        # Manager cannot access foreign company
        get_res = client.get(f'/api/accounts/companies/{self.company2.id}/')
        self.assertEqual(get_res.status_code, status.HTTP_403_FORBIDDEN)

        # Manager cannot delete own company
        del_res = client.delete(f'/api/accounts/companies/{self.company1.id}/')
        self.assertEqual(del_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_cannot_elevate_privileges(self):
        client = APIClient()
        client.force_authenticate(user=self.staff)

        # Staff cannot patch their own role to admin
        patch_res = client.patch(f'/api/accounts/users/{self.staff.id}/', {'role': 'admin'})
        self.assertEqual(patch_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.role, 'staff')

        # Staff cannot delete other users
        del_res = client.delete(f'/api/accounts/users/{self.manager.id}/')
        self.assertEqual(del_res.status_code, status.HTTP_403_FORBIDDEN)
