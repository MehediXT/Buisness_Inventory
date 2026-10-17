from rest_framework import serializers
from .models import User, Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'company', 'phone']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Non-admins cannot alter their or others' company
            if 'company' in attrs and request.user.role != 'admin':
                target_company = attrs['company']
                if request.user.company and target_company != request.user.company:
                    raise serializers.ValidationError({'company': "You cannot assign users to another company."})

            # Staff cannot alter roles at all; Managers can only assign 'staff'
            if 'role' in attrs:
                current_role = getattr(self.instance, 'role', None)
                if request.user.role == 'staff' and attrs['role'] != current_role:
                    raise serializers.ValidationError({'role': "Staff members cannot change user roles."})
                if request.user.role == 'manager' and attrs['role'] not in ['staff']:
                    raise serializers.ValidationError({'role': "Managers cannot assign admin or manager roles."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
