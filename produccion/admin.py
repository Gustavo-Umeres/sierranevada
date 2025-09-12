from django.contrib import admin
from .models import Bastidor, Artesa, Jaula, Lote, RegistroDiario, RegistroMortalidad

@admin.register(Bastidor)
class BastidorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'capacidad_maxima_unidades', 'esta_disponible')
    list_filter = ('esta_disponible',)
    readonly_fields = ('codigo',)

@admin.register(Artesa)
class ArtesaAdmin(admin.ModelAdmin):
    # 'talla_min_cm' y 'talla_max_cm' han sido eliminados de list_display
    list_display = ('codigo', 'capacidad_maxima_unidades', 'esta_disponible')
    list_filter = ('esta_disponible',)
    readonly_fields = ('codigo',)
    # 'talla_min_cm' y 'talla_max_cm' han sido eliminados de fields
    fields = ('capacidad_maxima_unidades', 'esta_disponible')

@admin.register(Jaula)
class JaulaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'capacidad_maxima_unidades', 'esta_disponible')
    list_filter = ('esta_disponible',)
    readonly_fields = ('codigo',)

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    # Aquí es donde se deben mostrar los campos de talla
    list_display = ('codigo_lote', 'etapa_actual', 'cantidad_total_peces', 'ubicacion_actual', 'talla_min_cm', 'talla_max_cm', 'fecha_ingreso_etapa')
    list_filter = ('etapa_actual',)
    readonly_fields = ('codigo_lote',)
    
    @admin.display(description='Ubicación Actual')
    def ubicacion_actual(self, obj):
        if obj.bastidor:
            return obj.bastidor.codigo
        if obj.artesa:
            return obj.artesa.codigo
        if obj.jaula:
            return obj.jaula.codigo
        return "Sin asignar"

@admin.register(RegistroDiario)
class RegistroDiarioAdmin(admin.ModelAdmin):
    list_display = ('lote', 'fecha', 'alimentacion_realizada', 'limpieza_realizada')
    list_filter = ('fecha', 'alimentacion_realizada', 'limpieza_realizada')

@admin.register(RegistroMortalidad)
class RegistroMortalidadAdmin(admin.ModelAdmin):
    list_display = ('lote', 'fecha', 'cantidad', 'registrado_por')
    list_filter = ('fecha',)