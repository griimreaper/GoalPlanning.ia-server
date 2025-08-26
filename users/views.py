# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .serializers import UserSerializer
from .models import User
from django.contrib.auth.hashers import check_password
from rest_framework.authtoken.models import Token  # usar token DRF
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    email = request.data.get('email')

    # Verificar si el email ya existe
    if User.objects.filter(email=email).exists():
        return Response({"error": "El email ya está registrado"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "token": token.key
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    if not email or not password:
        return Response({"error": "Email y contraseña requeridos"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        if check_password(password, user.password):
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "token": token.key
            }, status=status.HTTP_200_OK)
        return Response({"error": "Contraseña incorrecta"}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
