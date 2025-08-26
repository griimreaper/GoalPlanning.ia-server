# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .serializers import UserSerializer
from .models import User
from django.contrib.auth.hashers import check_password
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.db import DatabaseError

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    email = request.data.get('email')
    password = request.data.get('password')
    name = request.data.get('name')

    # Validate required fields
    if not email or not password or not name:
        return Response(
            {"error": "Name, email, and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "Email is already registered"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Serialization
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "token": token.key
            }, status=status.HTTP_201_CREATED)
        except DatabaseError:
            return Response(
                {"error": "Error registering the user"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    # Validate required fields
    if not email or not password:
        return Response(
            {"error": "Email and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except DatabaseError:
        return Response(
            {"error": "Database error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Validate password
    if not check_password(password, user.password):
        return Response(
            {"error": "Incorrect password"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "token": token.key
        }, status=status.HTTP_200_OK)
    except DatabaseError:
        return Response(
            {"error": "Error generating session token"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
