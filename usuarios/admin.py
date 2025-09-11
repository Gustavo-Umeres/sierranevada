from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PreguntaSeguridad

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    # CORRECCIÓN: Eliminamos la referencia a 'rol' de estas tuplas
    fieldsets = UserAdmin.fieldsets + (
        ('Información Extra', {'fields': ('dni', 'pregunta_seguridad', 'respuesta_seguridad')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('dni', 'pregunta_seguridad', 'respuesta_seguridad')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(PreguntaSeguridad)