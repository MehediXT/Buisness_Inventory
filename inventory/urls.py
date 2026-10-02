from django.urls import path
from .views import CustomerListCreateView, CustomerDetailView, CategoryListCreateView, CategoryDetailView, ProductListCreateView, ProductDetailView


urlpatterns = [
        path('customers/', CustomerListCreateView.as_view()),
        path('customers/<int:pk>/', CustomerDetailView.as_view()),
        path('categories/', CategoryListCreateView.as_view()),
        path('categories/<int:pk>/', CategoryDetailView.as_view()),
        path('products/', ProductListCreateView.as_view()),
        path('products/<int:pk>/', ProductDetailView.as_view())

]
