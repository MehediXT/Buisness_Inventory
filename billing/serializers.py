from rest_framework import serializers
from django.db import transaction
from .models import Invoice, InvoiceItem
from inventory.models import Product, Customer


class InvoiceItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = InvoiceItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'subtotal']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'customer', 'customer_name', 'status', 'created_at', 'items', 'total']
        read_only_fields = ['company', 'created_by']
        extra_kwargs = {
            'invoice_number': {'required': False, 'allow_blank': True}
        }

    def validate(self, attrs):
        request = self.context.get('request')
        company = self.context.get('company')
        if not company and request and hasattr(request.user, 'company'):
            company = request.user.company

        # If creating or updating customer, verify customer belongs to company
        customer = attrs.get('customer') or (self.instance.customer if self.instance else None)
        if company and customer and customer.company_id != company.id:
            raise serializers.ValidationError({'customer': "Customer does not belong to your company."})

        # Validate items if provided
        items_data = attrs.get('items')
        if items_data is not None:
            if len(items_data) == 0:
                raise serializers.ValidationError({'items': "An invoice must contain at least one item."})

            for item in items_data:
                product = item.get('product')
                if company and product and product.company_id != company.id:
                    raise serializers.ValidationError({'items': f"Product {product.name} does not belong to your company."})

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        with transaction.atomic():
            invoice = Invoice.objects.create(**validated_data)
            for item in items_data:
                product_id = item['product'].id
                quantity = item['quantity']

                # Lock product row and verify stock
                product = Product.objects.select_for_update().get(id=product_id)
                if product.stock_quantity < quantity:
                    raise serializers.ValidationError(
                        f"Insufficient stock for product '{product.name}'. Available: {product.stock_quantity}, requested: {quantity}."
                    )
                product.stock_quantity -= quantity
                product.save(update_fields=['stock_quantity'])

                InvoiceItem.objects.create(invoice=invoice, **item)
        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if items_data is not None:
                # 1. Restore stock for previously associated items
                for old_item in instance.items.select_related('product'):
                    Product.objects.filter(id=old_item.product_id).select_for_update()
                    old_item.product.stock_quantity += old_item.quantity
                    old_item.product.save(update_fields=['stock_quantity'])

                # 2. Delete old items
                instance.items.all().delete()

                # 3. Create new items and deduct stock
                for item in items_data:
                    product_id = item['product'].id
                    quantity = item['quantity']

                    product = Product.objects.select_for_update().get(id=product_id)
                    if product.stock_quantity < quantity:
                        raise serializers.ValidationError(
                            f"Insufficient stock for product '{product.name}'. Available: {product.stock_quantity}, requested: {quantity}."
                        )
                    product.stock_quantity -= quantity
                    product.save(update_fields=['stock_quantity'])

                    InvoiceItem.objects.create(invoice=instance, **item)

        return instance
