from django.urls import path
from .views import (
    InvoiceListCreateView, InvoiceDetailView, InvoicePrintView,
    DashboardSummaryView, SalesReportView,
)

urlpatterns = [
    path('invoices/', InvoiceListCreateView.as_view()),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view()),
    path('invoices/<int:pk>/print/', InvoicePrintView.as_view(), name='invoice-print'),
    path('dashboard/summary/', DashboardSummaryView.as_view()),
    path('reports/sales/', SalesReportView.as_view()),
]
