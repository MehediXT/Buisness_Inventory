from .models import User, Company
from .serializers import UserSerializer, CompanySerializer
from rest_framework import viewsets, permissions
from .permissions import IsAdmin, IsAdminManager
from rest_framework import status, APIView
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
    permission_classes = [IsAdminOrManager]

    def get_object(self, pk):
        try:
            return Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return None

    def get(self, request, pk):
        if request.user.role == "manager":
            user = request.user
            if not user.company.id== pk:
                return Response(
                    {"detail": "You do not have permission to perform this action."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        company = self.get_object(pk)
        if not company:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CompanySerializer(company).data)

    def put(self, request, pk):
        company = self.get_object(pk)
        if not company:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        company = self.get_object(pk)
        if not company:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        company = self.get_object(pk)
        if not company:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserListCreateView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        if request.user.role == "manager":
            users = User.objects.filter(company__id=request.user.company.id)
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role == "manager":
            if not request.data.get("role") == "staff":
                return Response(
                        {"detail": "You can not have the permission to create manager or admin."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            if not request.data.get("company") == request.user.company.id:
                return Response(
                        {"detail": f"You can not have the permission to create user in company {request.data.get('company')}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(company=request.user.company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        try:
            return User.objects.get(pk=pk, company=request.user.company)
        except User.DoesNotExist:
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
        serializer = UserSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        user = self.get_object(pk, request)
        if not user:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        user = self.get_object(pk, request)
        if not user:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
