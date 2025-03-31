# main/models.py - Modelos actualizados

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string
from django.utils import timezone

class CustomUser(AbstractUser):
    def generate_id():
        return get_random_string(24, allowed_chars='abcdef0123456789')
    
    id = models.CharField(
        primary_key=True,
        max_length=24,
        default=generate_id,
        editable=False
    )
    email = models.EmailField(unique=True)
    groups = models.ManyToManyField("auth.Group", blank=True)
    user_permissions = models.ManyToManyField("auth.Permission", blank=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email

class UserSession(models.Model):
    def generate_id():
        return get_random_string(24, allowed_chars='abcdef0123456789')
    
    id = models.CharField(
        primary_key=True, 
        max_length=24, 
        default=generate_id, 
        editable=False
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    session_data = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "user_sessions"
        
    def __str__(self):
        return f"{self.user.username} - {self.session_key[:8]}"

class Device(models.Model):
    def generate_id():
        return get_random_string(24, allowed_chars='abcdef0123456789')
        
    id = models.CharField(
        primary_key=True,
        max_length=24,
        default=generate_id,
        editable=False
    )
    nombre = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_fabricacion = models.DateField(auto_now_add=True)
    disponible = models.BooleanField(default=True)
    
    class Meta:
        db_table = "devices"
        
    def __str__(self):
        return f"{self.nombre} - {self.numero_serie}"

class UserDevice(models.Model):
    def generate_id():
        return get_random_string(24, allowed_chars='abcdef0123456789')
        
    id = models.CharField(
        primary_key=True,
        max_length=24,
        default=generate_id,
        editable=False
    )
    usuario_id = models.CharField(max_length=24)  
    dispositivo_id = models.CharField(max_length=24)  
    fecha_adquisicion = models.DateTimeField(auto_now_add=True)
    nombre_personalizado = models.CharField(max_length=100, blank=True, null=True)
    ubicacion = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = "user_devices"

class ConnectedAppliance(models.Model):
    def generate_id():
        return get_random_string(24, allowed_chars='abcdef0123456789')
        
    id = models.CharField(
        primary_key=True,
        max_length=24,
        default=generate_id,
        editable=False
    )
    user_device = models.ForeignKey(UserDevice, on_delete=models.CASCADE, related_name='electrodomesticos')
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)  
    icono = models.CharField(max_length=50, blank=True, null=True)
    voltaje = models.IntegerField(default=120)
    fecha_conexion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    apagado_periodico = models.JSONField(blank=True, null=True)  
    
    class Meta:
        db_table = "connected_appliances"
        
    def __str__(self):
        return f"{self.nombre} - {self.user_device.usuario_id}"

class ApplianceConsumption(models.Model):
    def generate_id():
        return get_random_string(24, allowed_chars='abcdef0123456789')
        
    id = models.CharField(
        primary_key=True,
        max_length=24,
        default=generate_id,
        editable=False
    )
    appliance = models.ForeignKey(ConnectedAppliance, on_delete=models.CASCADE, related_name='consumos')
    fecha = models.DateTimeField(auto_now_add=True)
    potencia = models.FloatField(default=0)  # en watts
    corriente = models.FloatField(default=0)  # en amperios
    voltaje = models.FloatField(default=0)  # en voltios
    consumo = models.FloatField(default=0)  # en kWh
    frecuencia = models.FloatField(default=60.0)
    
    class Meta:
        db_table = "appliance_consumption"
        
    def __str__(self):
        return f"{self.appliance.nombre} - {self.fecha}"
    
class ApplianceAlert(models.Model):
    def generate_id():
        return get_random_string(24, allowed_chars='abcdef0123456789')
        
    id = models.CharField(
        primary_key=True,
        max_length=24,
        default=generate_id,
        editable=False
    )
    appliance = models.ForeignKey(ConnectedAppliance, on_delete=models.CASCADE, related_name='alertas')
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=50)  
    mensaje = models.TextField()
    atendida = models.BooleanField(default=False)
    
    class Meta:
        db_table = "appliance_alerts"
        
    def __str__(self):
        return f"{self.appliance.nombre} - {self.tipo} - {self.fecha}"
    
class AuthToken(models.Model):
    def generate_id():
        return get_random_string(40, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    
    id = models.CharField(primary_key=True, max_length=40, default=generate_id, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tokens')
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    device_info = models.TextField(blank=True, null=True)  # Para almacenar info del dispositivo móvil
    
    class Meta:
        db_table = "auth_tokens"
        
    def __str__(self):
        return f"{self.user.username} - {self.id[:8]}"
    
    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

class ApplianceControlState(models.Model):
    def generate_id():
        return get_random_string(24, allowed_chars='abcdef0123456789')
        
    id = models.CharField(
        primary_key=True,
        max_length=24,
        default=generate_id,
        editable=False
    )
    appliance = models.OneToOneField(ConnectedAppliance, on_delete=models.CASCADE, related_name='control_state')
    state = models.BooleanField(default=True)  # True = ON, False = OFF
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "appliance_control_states"
        
    def __str__(self):
        return f"{self.appliance.nombre} - {'ON' if self.state else 'OFF'}"
    
# main/models.py - Añadir esta clase al final
class ApplianceAutoShutdown(models.Model):
    def generate_id():
        return get_random_string(24, allowed_chars='abcdef0123456789')
        
    id = models.CharField(
        primary_key=True,
        max_length=24,
        default=generate_id,
        editable=False
    )
    appliance = models.OneToOneField(ConnectedAppliance, on_delete=models.CASCADE, related_name='auto_shutdown')
    hours_on = models.IntegerField(default=0)
    minutes_on = models.IntegerField(default=0)
    hours_off = models.IntegerField(default=0)
    minutes_off = models.IntegerField(default=0)
    enabled = models.BooleanField(default=False)
    current_state = models.BooleanField(default=True)  # True = ON, False = OFF
    last_switch = models.DateTimeField(auto_now_add=True)
    next_switch = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "appliance_auto_shutdown"
        
    def __str__(self):
        return f"{self.appliance.nombre} - {'Activo' if self.enabled else 'Inactivo'}"

    def save(self, *args, **kwargs):
        # Asegurarse de que next_switch se actualice correctamente
        if not self.next_switch or self.next_switch <= timezone.now():
            self.next_switch = timezone.now() + timezone.timedelta(
                hours=self.hours_on if self.current_state else self.hours_off,
                minutes=self.minutes_on if self.current_state else self.minutes_off
            )
        super().save(*args, **kwargs)