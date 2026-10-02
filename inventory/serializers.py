from rest_framework import serializers
from .models import Customer, Category, Product


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["__all__"]
        read_only_fields = ['company']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["__all__"]
        read_only_fields = ['company']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    class Meta:
        model = Product
        fields = ["__all__"]
        read_only_fields = ['company']
