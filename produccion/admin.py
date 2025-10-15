from django.contrib import admin
import datetime
from .models import Bastidor, Artesa, Jaula, Lote, RegistroDiario, RegistroMortalidad

@admin.register(Bastidor)
class BastidorAdmin(admin.ModelAdmin):
    # Sin cambios aquí, Bastidor sigue usando unidades
    list_display = ('codigo', 'capacidad_maxima_unidades', 'esta_disponible')
    list_filter = ('esta_disponible',)
    readonly_fields = ('codigo',)

@admin.register(Artesa)
class ArtesaAdmin(admin.ModelAdmin):
    # --- LÍNEAS CORREGIDAS ---
    list_display = ('codigo', 'forma', 'capacidad_maxima_kg', 'biomasa_actual', 'biomasa_disponible_display')
    list_filter = ('forma',) # Se quita 'esta_disponible'
    readonly_fields = ('codigo',)

    @admin.display(description='Biomasa Disponible (kg)')
    def biomasa_disponible_display(self, obj):
        # Muestra la biomasa disponible calculada por la propiedad del modelo
        return obj.biomasa_disponible

@admin.register(Jaula)
class JaulaAdmin(admin.ModelAdmin):
    # --- LÍNEAS CORREGIDAS ---
    list_display = ('codigo', 'tipo', 'forma', 'capacidad_maxima_kg', 'biomasa_actual', 'biomasa_disponible_display')
    list_filter = ('tipo', 'forma',) # Se quita 'esta_disponible'
    readonly_fields = ('codigo',)

    @admin.display(description='Biomasa Disponible (kg)')
    def biomasa_disponible_display(self, obj):
        # Muestra la biomasa disponible calculada por la propiedad del modelo
        return obj.biomasa_disponible
@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('codigo_lote', 'etapa_actual', 'cantidad_total_peces', 'peso_promedio_pez_gr', 'biomasa_kg', 'ubicacion_actual', 'fecha_ingreso_etapa')
    list_filter = ('etapa_actual',)
    readonly_fields = ('codigo_lote', 'biomasa_kg')
    actions = ['avanzar_un_dia', 'avanzar_siete_dias']

    @admin.display(description='Ubicación Actual')
    def ubicacion_actual(self, obj):
        if obj.bastidor:
            return obj.bastidor.codigo
        if obj.artesa:
            return obj.artesa.codigo
        if obj.jaula:
            return obj.jaula.codigo
        return "Sin asignar"

    @admin.display(description='Biomasa (kg)')
    def biomasa_kg(self, obj):
        # Muestra la biomasa calculada por la propiedad del modelo
        return obj.biomasa_kg

    @admin.action(description='Avanzar fecha de ingreso 1 día')
    def avanzar_un_dia(self, request, queryset):
        for lote in queryset:
            lote.fecha_ingreso_etapa -= datetime.timedelta(days=1)
            lote.save()
        self.message_user(request, "Se retrocedió la fecha de los lotes seleccionados en 1 día.")

    @admin.action(description='Avanzar fecha de ingreso 7 días')
    def avanzar_siete_dias(self, request, queryset):
        for lote in queryset:
            lote.fecha_ingreso_etapa -= datetime.timedelta(days=7)
            lote.save()
        self.message_user(request, "Se retrocedió la fecha de los lotes seleccionados en 7 días.")

@admin.register(RegistroDiario)
class RegistroDiarioAdmin(admin.ModelAdmin):
    list_display = ('lote', 'fecha', 'alimentacion_realizada', 'limpieza_realizada')
    list_filter = ('fecha', 'alimentacion_realizada', 'limpieza_realizada')

@admin.register(RegistroMortalidad)
class RegistroMortalidadAdmin(admin.ModelAdmin):
    list_display = ('lote', 'fecha', 'cantidad', 'registrado_por')
    list_filter = ('fecha',)