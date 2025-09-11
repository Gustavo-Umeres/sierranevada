from django.contrib.auth.models import AbstractUser
from django.db import models

class PreguntaSeguridad(models.Model):
    texto = models.CharField(max_length=255)
    def __str__(self): return self.texto

class CustomUser(AbstractUser):
    # ¡Hemos eliminado el campo 'rol' definitivamente!
    dni = models.CharField(max_length=8, unique=True, null=True, blank=True)
    pregunta_seguridad = models.ForeignKey(PreguntaSeguridad, on_delete=models.SET_NULL, null=True, blank=True)
    respuesta_seguridad = models.CharField(max_length=255, null=True, blank=True)
    
    # Mantenemos la relación estándar de Django con Grupos y Permisos
    groups = models.ManyToManyField('auth.Group', related_name='customuser_set', blank=True, verbose_name='grupos')
    user_permissions = models.ManyToManyField('auth.Permission', related_name='customuser_set', blank=True)

    def __str__(self):
        return self.username