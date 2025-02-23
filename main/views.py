from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import get_user_model

from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()


def index(request):
    return render(request, 'index.html')

def home(request):
    return render(request, 'home.html');

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

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

def loginUserManager(request):
    if request.method == "GET":
        return render(request, 'login.html')

    if request.method == "POST":
        username_or_email = request.POST.get("username_or_email")  # Puede ser email o username
        password = request.POST.get("password")

        print(username_or_email)
        print(password)

        user = authenticate(request, username=username_or_email, password=password) 

        if user is not None:
            login(request, user)
            print("mandando a home")
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Credenciales incorrectas'})

