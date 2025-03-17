from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json

# No importes los modelos aquí para evitar la importación circular
# Importamos los modelos dentro de cada función donde se necesitan

User = get_user_model()


class SocialAccountAdapter:
    """Adaptador para allauth"""
    pass


def index(request):
    return render(request, 'index.html')

def home(request):
    return render(request, 'home.html')

def download(request):
    return render(request, 'download.html')

def aboutus(request):
    return render(request, 'about-us.html')

def productos(request):
    return render(request, 'productos.html')
def devices(request):
    return render(request, 'devices.html')

def device_info(request):
    return render(request, 'devices-info.html')

def optimiza_consumo(request):
    return render(request, 'optimiza-consumo.html')

def conoce_mas(request):
    return render(request, 'conoce-mas.html')

def registerUserManager(request):
    if request.method == "GET":
        return render(request, 'login.html')

    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return HttpResponse("El usuario ya existe")

        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            return redirect('login')
        except Exception as e:
            return HttpResponse(f"Error al crear usuario: {e}")

def loginUserManager(request):
    if request.method == "GET":
        return render(request, 'login.html')

    if request.method == "POST":
        username_or_email = request.POST.get("username_or_email")  
        password = request.POST.get("password")

        user = authenticate(request, username=username_or_email, password=password) 

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Credenciales incorrectas'})

@login_required
def logoutUser(request):
    # Implementaremos la lógica de sesiones después de resolver el problema de importación
    logout(request)
    return redirect('login')