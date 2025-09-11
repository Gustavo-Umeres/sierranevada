from django.contrib import admin
from .models import Bastidor, Artesa, Jaula, Lote, RegistroDiario, RegistroMortalidad

admin.site.register(Bastidor)
admin.site.register(Artesa)
admin.site.register(Jaula)
admin.site.register(Lote)
admin.site.register(RegistroDiario)
admin.site.register(RegistroMortalidad)