# EnergySafe/urls.py - Actualizado
from django.contrib import admin
from django.urls import include, path
from main import api_views, views, device_views

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

    path('api/consumption/latest/<str:appliance_id>/', api_views.get_latest_consumption, name='get_latest_consumption'),
    path('get-csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    path('mobile/login/', views.mobile_login, name='mobile_login'),

    # Rutas para dispositivos
    path('devices/appliance/add/', device_views.add_appliance, name='add_appliance'),
    path('devices/appliance/<str:appliance_id>/', device_views.appliance_details, name='appliance_details'),
    path('devices/appliance/<str:appliance_id>/', device_views.appliance_details, name='devices-info'),

    path('blog/', views.blog, name='blog'),
    path('soporte/', views.soporte, name='soporte'),
    path('aviso-de-privacidad/', views.aviso_de_privacidad, name='aviso_de_privacidad'),

    # Mantener esta ruta para compatibilidad
    path('devices-info/', views.device_info, name='devices-info'),

    # API
    path('api/device-readings/', api_views.device_readings, name='device_readings'),
    path('api/device-alerts/', api_views.device_alerts, name='device_alerts'),
    path('api/alerts/attend/<str:alert_id>/', api_views.mark_alert_attended, name='mark_alert_attended'),

    # Nuevas rutas para control de dispositivos
    path('api/device-control/', api_views.device_control, name='device_control'),
    path('api/device-control-state/', api_views.device_control_state, name='device_control_state'),

    # API para aplicación móvil
    path('api/mobile/login/', views.mobile_login, name='api_mobile_login'),
    path('api/mobile/register/', views.mobile_register, name='api_mobile_register'),
    path('api/mobile/verify-token/', views.verify_token, name='api_verify_token'),
    path('api/mobile/logout/', views.mobile_logout, name='api_mobile_logout'),
    path('api/mobile/appliances/', api_views.get_user_appliances, name='api_mobile_appliances'),
    path('api/mobile/appliance/<str:appliance_id>/data/', api_views.get_appliance_data, name='api_appliance_data'),

    # En urlpatterns, agregar estas rutas
    path('devices/device/delete/', device_views.delete_device, name='delete_device'),
    path('devices/device/edit/', device_views.edit_device, name='edit_device'),
    path('devices/appliance/delete/', device_views.delete_appliance, name='delete_appliance'),
    path('devices/appliance/edit/', device_views.edit_appliance, name='edit_appliance'),

    # Agregar esta línea a urlpatterns en EnergySafe/urls.py
# Justo debajo de path('api/device-control/', api_views.device_control, name='device_control'),

path('api/device-auto-shutdown/', api_views.device_auto_shutdown, name='device_auto_shutdown'),
    path('api/device-auto-shutdown-config/', api_views.device_auto_shutdown_config, name='device_auto_shutdown_config'),
    ]