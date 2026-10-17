from django.test import TestCase
from django.db.utils import IntegrityError
from accounts.models import Company, User
from inventory.models import Customer, Category, Product
from inventory.serializers import CustomerSerializer, CategorySerializer, ProductSerializer
from rest_framework.test import APIClient
from rest_framework import status


class InventoryTests(TestCase):
    def setUp(self):
        self.company1 = Company.objects.create(name="Company One")
        self.company2 = Company.objects.create(name="Company Two")

        self.user1 = User.objects.create_user(
            username="user1", password="password123", company=self.company1, role="staff"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

    def test_serializers_validity(self):
        # Verify fields = '__all__' fix resolves ImproperlyConfigured
        customer = Customer.objects.create(company=self.company1, name="Alice")
        category = Category.objects.create(company=self.company1, name="Electronics")
        product = Product.objects.create(
            company=self.company1, category=category, name="Laptop", sku="SKU-001", price=999.99, stock_quantity=10
        )

        c_data = CustomerSerializer(customer).data
        self.assertEqual(c_data['name'], "Alice")

        cat_data = CategorySerializer(category).data
        self.assertEqual(cat_data['name'], "Electronics")

        p_data = ProductSerializer(product).data
        self.assertEqual(p_data['name'], "Laptop")
        self.assertEqual(p_data['category_name'], "Electronics")

    def test_sku_uniqueness_per_company(self):
        # Two different companies can use the same SKU
        Product.objects.create(company=self.company1, name="Widget 1", sku="WIDGET-01", price=10, stock_quantity=5)
        Product.objects.create(company=self.company2, name="Widget 2", sku="WIDGET-01", price=15, stock_quantity=8)

        # Same company cannot use duplicate SKU
        with self.assertRaises(IntegrityError):
            Product.objects.create(company=self.company1, name="Widget Duplicate", sku="WIDGET-01", price=20, stock_quantity=2)

    def test_product_list_create_api(self):
        response = self.client.post('/api/inventory/products/', {
            'name': 'Mouse',
            'sku': 'MOUSE-01',
            'price': '25.00',
            'stock_quantity': 50
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Mouse')

        get_res = self.client.get('/api/inventory/products/')
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_res.data), 1)
