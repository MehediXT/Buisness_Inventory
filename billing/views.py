from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import status
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models import Count, Sum, F
from accounts.authentication import JWTQueryParamAuthentication
from .models import Invoice, InvoiceItem
from .serializers import InvoiceSerializer
from inventory.models import Product


class InvoiceListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        invoices = (
            Invoice.objects
            .filter(company=request.user.company)
            .select_related('customer')
            .prefetch_related('items__product')
        )
        return Response(InvoiceSerializer(invoices, many=True).data)

    def post(self, request):
        serializer = InvoiceSerializer(
            data=request.data,
            context={'request': request, 'company': request.user.company}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(company=request.user.company, created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InvoiceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        try:
            return (
                Invoice.objects
                .select_related('customer')
                .prefetch_related('items__product')
                .get(pk=pk, company=request.user.company)
            )
        except Invoice.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk, request)
        if not obj:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(InvoiceSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk, request)
        if not obj:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = InvoiceSerializer(
            obj,
            data=request.data,
            context={'request': request, 'company': request.user.company}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        obj = self.get_object(pk, request)
        if not obj:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = InvoiceSerializer(
            obj,
            data=request.data,
            partial=True,
            context={'request': request, 'company': request.user.company}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        obj = self.get_object(pk, request)
        if not obj:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvoicePrintView(APIView):
    """Printable invoice page (no PDF library needed).

    Returns a print-optimised HTML document; the browser turns it into a PDF
    via its own print dialog (Cmd/Ctrl+P -> Save as PDF).

    Because a browser cannot send an Authorization header when the URL is opened
    directly, the access token may be passed as `?token=<access token>`.
    Add `?auto=0` to skip the automatic print dialog.
    """

    authentication_classes = [JWTQueryParamAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            invoice = (
                Invoice.objects
                .select_related('customer', 'company', 'created_by')
                .prefetch_related('items__product')
                .get(pk=pk, company=request.user.company)
            )
        except Invoice.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        html_string = render_to_string('billing/invoice_pdf.html', {
            'invoice': invoice,
            'company': invoice.company,
            'auto_print': request.query_params.get('auto', '1') != '0',
        })

        response = HttpResponse(html_string, content_type='text/html; charset=utf-8')
        response['Content-Disposition'] = f'inline; filename="{invoice.invoice_number}.html"'
        return response


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.company
        invoices = Invoice.objects.filter(company=company)

        # Database aggregation instead of Python in-memory sum
        total_revenue = (
            InvoiceItem.objects
            .filter(invoice__company=company, invoice__status='paid')
            .aggregate(total=Sum(F('quantity') * F('unit_price')))['total'] or 0
        )

        # Bestselling products by quantity sold
        top_products = list(
            Product.objects.filter(company=company, invoiceitem__invoice__status='paid')
            .annotate(total_sold=Sum('invoiceitem__quantity'))
            .order_by('-total_sold')[:5]
            .values('id', 'name', 'stock_quantity', 'total_sold')
        )
        if not top_products:
            top_products = list(
                Product.objects.filter(company=company)[:5]
                .values('id', 'name', 'stock_quantity')
            )

        data = {
            'total_invoices': invoices.count(),
            'total_revenue': total_revenue,
            'invoices_by_status': list(invoices.values('status').annotate(count=Count('id'))),
            'low_stock_products': list(
                Product.objects.filter(company=company, stock_quantity__lte=5)
                .values('id', 'name', 'stock_quantity')
            ),
            'top_products': top_products,
        }
        return Response(data)


class SalesReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.company
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')

        qs = (
            Invoice.objects
            .filter(company=company, status='paid')
            .select_related('customer')
            .prefetch_related('items')
        )
        if from_date:
            qs = qs.filter(created_at__date__gte=from_date)
        if to_date:
            qs = qs.filter(created_at__date__lte=to_date)

        report = [{
            'invoice_number': inv.invoice_number,
            'customer': inv.customer.name if inv.customer else 'N/A',
            'date': inv.created_at,
            'total': inv.total,
        } for inv in qs]

        return Response({'count': len(report), 'results': report})
