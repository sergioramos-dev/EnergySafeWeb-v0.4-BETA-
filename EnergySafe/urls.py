# EnergySafe/urls.py - Versión mínima
from django.contrib import admin
from django.urls import include, path
from main import views, device_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index),
    path('home/', views.home, name='home'),
    path('login/', views.loginUserManager, name='login'),
    path('register/', views.registerUserManager, name='register'),
    path('logout/', views.logoutUser, name='logout'),
    path('download/', views.download, name='download'),
    path('accounts/', include('allauth.urls')),
    path('about-us/', views.aboutus, name='aboutus'),
    path('products/', views.productos, name='productos'),
    path('optimiza-consumo/', views.optimiza_consumo, name='optimiza_consumo'),
    path('conoce-mas/', views.conoce_mas, name='conoce_mas'),
    
    # Rutas simplificadas para dispositivos
    path('devices/', device_views.devices_dashboard, name='devices'),
    path('devices/verify/<str:numero_serie>/', device_views.verify_energy_safe, name='verify_device'),
    path('devices/register/', device_views.register_energy_safe, name='register_device'),
    # En EnergySafe/urls.py
    path('devices/appliance/add/', device_views.add_appliance, name='add_appliance'),
    path('devices/appliance/<str:appliance_id>/', device_views.appliance_details, name='appliance_details'),
    
    # Mantener esta ruta para compatibilidad
    path('devices-info/', views.device_info, name='devices-info'),
]