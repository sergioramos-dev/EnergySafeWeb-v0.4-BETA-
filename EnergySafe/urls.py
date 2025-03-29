# EnergySafe/urls.py - Versión mínima
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
    # Add this to EnergySafe/urls.py in the urlpatterns list
    path('api/consumption/latest/<str:appliance_id>/', api_views.get_latest_consumption, name='get_latest_consumption'),
        path('get-csrf-token/', views.get_csrf_token, name='get_csrf_token'),
            path('mobile/login/', views.mobile_login, name='mobile_login'),



    # En EnergySafe/urls.py
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

    path('api/device-readings/', api_views.device_readings, name='device_readings'),
    path('api/device-alerts/', api_views.device_alerts, name='device_alerts'),

    # Añade esta línea a tus urlpatterns
path('api/alerts/attend/<str:alert_id>/', api_views.mark_alert_attended, name='mark_alert_attended'),

# Añade esta línea a tus urlpatterns
path('api/alerts/attend/<str:alert_id>/', api_views.mark_alert_attended, name='mark_alert_attended'),

# Añadir estas líneas a EnergySafe/urls.py en el urlpatterns

# API para aplicación móvil
path('api/mobile/login/', views.mobile_login, name='api_mobile_login'),
path('api/mobile/register/', views.mobile_register, name='api_mobile_register'),
path('api/mobile/verify-token/', views.verify_token, name='api_verify_token'),
path('api/mobile/logout/', views.mobile_logout, name='api_mobile_logout'),

# Add this to EnergySafe/urls.py in the urlpatterns list

# API for mobile app - user appliances
path('api/mobile/appliances/', api_views.get_user_appliances, name='api_mobile_appliances'),
# Add this to EnergySafe/urls.py in the urlpatterns list

# API for mobile app - appliance data
path('api/mobile/appliance/<str:appliance_id>/data/', api_views.get_appliance_data, name='api_appliance_data'),
]

