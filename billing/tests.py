from django.test import TestCase
from accounts.models import Company, User
from inventory.models import Customer, Product
from billing.models import Invoice, InvoiceItem
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken


class BillingTests(TestCase):
    def setUp(self):
        self.company1 = Company.objects.create(name="Company A")
        self.company2 = Company.objects.create(name="Company B")

        self.user1 = User.objects.create_user(
            username="user_a", password="password123", company=self.company1, role="manager"
        )
        self.user2 = User.objects.create_user(
            username="user_b", password="password123", company=self.company2, role="manager"
        )

        self.customer1 = Customer.objects.create(company=self.company1, name="Acme Corp")
        self.customer2 = Customer.objects.create(company=self.company2, name="Beta LLC")

        self.product1 = Product.objects.create(
            company=self.company1, name="Keyboard", sku="KB-01", price=50.00, stock_quantity=10
        )
        self.product2 = Product.objects.create(
            company=self.company2, name="Monitor", sku="MN-01", price=200.00, stock_quantity=5
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

    def test_invoice_creation_deducts_stock(self):
        payload = {
            'customer': self.customer1.id,
            'status': 'paid',
            'items': [
                {'product': self.product1.id, 'quantity': 3, 'unit_price': '50.00'}
            ]
        }
        response = self.client.post('/api/billing/invoices/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check stock deduction
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 7)

        # Check total
        invoice = Invoice.objects.get(id=response.data['id'])
        self.assertEqual(invoice.total, 150.00)

    def test_invoice_creation_fails_when_stock_insufficient(self):
        payload = {
            'customer': self.customer1.id,
            'items': [
                {'product': self.product1.id, 'quantity': 15, 'unit_price': '50.00'}
            ]
        }
        response = self.client.post('/api/billing/invoices/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 10)

    def test_cross_tenant_isolation(self):
        # Trying to bill customer from Company 2
        payload = {
            'customer': self.customer2.id,
            'items': [
                {'product': self.product1.id, 'quantity': 1, 'unit_price': '50.00'}
            ]
        }
        response = self.client.post('/api/billing/invoices/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Customer does not belong to your company", str(response.data))

        # Trying to bill product from Company 2
        payload2 = {
            'customer': self.customer1.id,
            'items': [
                {'product': self.product2.id, 'quantity': 1, 'unit_price': '200.00'}
            ]
        }
        response2 = self.client.post('/api/billing/invoices/', payload2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not belong to your company", str(response2.data))

    def test_invoice_update_restores_and_deducts_stock(self):
        # Create invoice with 3 keyboards (stock: 10 -> 7)
        create_payload = {
            'customer': self.customer1.id,
            'items': [
                {'product': self.product1.id, 'quantity': 3, 'unit_price': '50.00'}
            ]
        }
        create_res = self.client.post('/api/billing/invoices/', create_payload, format='json')
        invoice_id = create_res.data['id']
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 7)

        # Update invoice to 2 keyboards (should restore 3, deduct 2 -> stock: 8)
        update_payload = {
            'customer': self.customer1.id,
            'items': [
                {'product': self.product1.id, 'quantity': 2, 'unit_price': '50.00'}
            ]
        }
        update_res = self.client.put(f'/api/billing/invoices/{invoice_id}/', update_payload, format='json')
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)

        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 8)

    def test_invoice_print_view_with_query_param_jwt(self):
        invoice = Invoice.objects.create(
            company=self.company1,
            customer=self.customer1,
            created_by=self.user1,
            status='paid'
        )
        InvoiceItem.objects.create(invoice=invoice, product=self.product1, quantity=1, unit_price=50.00)

        # Test with unauthenticated client using ?token= query param
        anon_client = APIClient()
        token = str(AccessToken.for_user(self.user1))
        response = anon_client.get(f'/api/billing/invoices/{invoice.id}/print/?token={token}&auto=0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text/html', response['Content-Type'])
        self.assertIn(invoice.invoice_number, response.content.decode('utf-8'))

    def test_dashboard_summary_and_sales_report(self):
        invoice = Invoice.objects.create(
            company=self.company1,
            customer=self.customer1,
            status='paid'
        )
        InvoiceItem.objects.create(invoice=invoice, product=self.product1, quantity=2, unit_price=50.00)

        dash_res = self.client.get('/api/billing/dashboard/summary/')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        self.assertEqual(dash_res.data['total_revenue'], 100.00)
        self.assertEqual(dash_res.data['total_invoices'], 1)

        report_res = self.client.get('/api/billing/reports/sales/')
        self.assertEqual(report_res.status_code, status.HTTP_200_OK)
        self.assertEqual(report_res.data['count'], 1)
