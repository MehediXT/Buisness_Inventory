from django.urls import path
from .views import CompanyListCreateView, CompanyDetailView, UserListCreateView, UserDetailView

urlpatterns = [
        path('users/', UserListCreateView.as_view()),
        path('users/<int:pk>/', UserDetailView.as_view()),
        path('companies/', CompanyListCreateView.as_view()),
        path('companies/<int:pk>/', CompanyDetailView.as_view())
    ]
