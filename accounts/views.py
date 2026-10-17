from .models import User, Company
from .serializers import UserSerializer, CompanySerializer
from .permissions import IsAdmin, IsAdminManager
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class CompanyListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompanyDetailView(APIView):
    permission_classes = [IsAdminManager]

    def get_object(self, pk):
        try:
            return Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return None

    def check_manager_access(self, request, pk):
        if request.user.role == "manager":
            if not request.user.company or request.user.company.id != pk:
                return False
        return True

    def get(self, request, pk):
        if not self.check_manager_access(request, pk):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        company = self.get_object(pk)
        if not company:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CompanySerializer(company).data)

    def put(self, request, pk):
        if not self.check_manager_access(request, pk):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        company = self.get_object(pk)
        if not company:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        if not self.check_manager_access(request, pk):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        company = self.get_object(pk)
        if not company:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        if request.user.role != "admin":
            return Response(
                {"detail": "Only admins can delete companies."},
                status=status.HTTP_403_FORBIDDEN
            )
        company = self.get_object(pk)
        if not company:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserListCreateView(APIView):
    permission_classes = [IsAdminManager]

    def get(self, request):
        if request.user.role == "manager":
            users = User.objects.filter(company=request.user.company)
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role == "manager":
            if request.data.get("role") != "staff":
                return Response(
                    {"detail": "You do not have permission to create manager or admin."},
                    status=status.HTTP_403_FORBIDDEN
                )
            company_id = request.data.get("company")
            if company_id and str(company_id) != str(request.user.company_id):
                return Response(
                    {"detail": "You do not have permission to create users for another company."},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = UserSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save(company=request.user.company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        serializer = UserSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        if 'company' not in serializer.validated_data and request.user.company:
            serializer.save(company=request.user.company)
        else:
            serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        user = request.user
        if user.role == 'admin':
            try:
                return User.objects.get(pk=pk)
            except User.DoesNotExist:
                return None
        elif user.role == 'manager':
            try:
                return User.objects.get(pk=pk, company=user.company)
            except User.DoesNotExist:
                return None
        else:
            if user.id == pk:
                return user
            return None

    def get(self, request, pk):
        user = self.get_object(pk, request)
        if not user:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSerializer(user).data)

    def put(self, request, pk):
        user = self.get_object(pk, request)
        if not user:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if request.user.role == 'manager' and user.role in ['admin', 'manager'] and user.id != request.user.id:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = UserSerializer(user, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        user = self.get_object(pk, request)
        if not user:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if request.user.role == 'manager' and user.role in ['admin', 'manager'] and user.id != request.user.id:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        if request.user.role == 'staff':
            return Response({'detail': 'Staff cannot delete user accounts.'}, status=status.HTTP_403_FORBIDDEN)
        user = self.get_object(pk, request)
        if not user:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if request.user.role == 'manager' and (user.role in ['admin', 'manager'] or user.id == request.user.id):
            return Response({'detail': 'Managers cannot delete administrators or managers.'}, status=status.HTTP_403_FORBIDDEN)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
