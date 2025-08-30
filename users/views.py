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
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from dotenv import load_dotenv
import os
from django.http import HttpResponseRedirect

load_dotenv()

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

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

def process_google_user(access_token):
    response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code != 200:
        return None, {"error": "Invalid Google token"}

    user_info = response.json()
    email = user_info["email"]
    name = user_info.get("name", email.split("@")[0])

    try:
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "name": name,
                "password": User.objects.make_random_password()
            }
        )
    except Exception as e:
        return None, {"error": str(e)}

    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }
    }, None


@api_view(["POST"])
@permission_classes([AllowAny])
def google(request):
    token = request.data.get("token")
    if not token:
        return Response({"error": "Token not provided"}, status=400)

    data, error = process_google_user(token)
    if error:
        return Response(error, status=400)
    return Response(data, status=200)


def google_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponseRedirect("goalplanning://redirect?error=missing_code")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("ALLOWED_HOSTS") + "/auth/google/callback/",
        "grant_type": "authorization_code",
    }
    r = requests.post(token_url, data=data)
    token_data = r.json()

    access_token = token_data.get("access_token")
    if not access_token:
        return HttpResponseRedirect("goalplanning://redirect?error=invalid_token")

    # Usar la misma lógica de creación/login
    user_data, error = process_google_user(access_token)
    if error:
        return HttpResponseRedirect("goalplanning://redirect?error=auth_failed")

    # Retornar el token JWT ya emitido por DRF
    return HttpResponseRedirect(
        f"goalplanning://redirect?access={user_data['access']}&refresh={user_data['refresh']}"
    )