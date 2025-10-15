from django.contrib import admin
from django.db.models import Sum, F
from django.utils import timezone
from .models import (
    Bastidor, Artesa, Jaula, Lote, RegistroDiario, 
    RegistroMortalidad, HistorialMovimiento, RegistroUnidad,Enfermedad 
)


# ================================================================
# REGISTRO DE UNIDADES
# ================================================================

@admin.register(Bastidor)
class BastidorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'capacidad_maxima_unidades', 'esta_disponible')
    list_filter = ('esta_disponible',)
    search_fields = ('codigo',)
    readonly_fields = ('codigo',)
    fieldsets = (
        (None, {
            'fields': ('capacidad_maxima_unidades',),
        }),
    )

@admin.register(Artesa)
class ArtesaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'forma', 'capacidad_maxima_kg', 'biomasa_actual_display', 'biomasa_disponible_display')
    list_filter = ('forma',)
    search_fields = ('codigo',)
    readonly_fields = ('codigo', 'capacidad_maxima_kg', 'biomasa_actual_display', 'biomasa_disponible_display')
    
    @admin.display(description='Biomasa Actual (kg)')
    def biomasa_actual_display(self, obj):
        # Muestra la biomasa actual calculada por la propiedad del modelo
        return f"{obj.biomasa_actual:.2f} kg"

    @admin.display(description='Biomasa Disponible (kg)')
    def biomasa_disponible_display(self, obj):
        # Muestra la biomasa disponible calculada por la propiedad del modelo
        return f"{obj.biomasa_disponible:.2f} kg"

@admin.register(Jaula)
class JaulaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'tipo', 'forma', 'capacidad_maxima_kg', 'biomasa_actual_display', 'biomasa_disponible_display')
    list_filter = ('tipo', 'forma',)
    search_fields = ('codigo',)
    readonly_fields = ('codigo', 'capacidad_maxima_kg', 'biomasa_actual_display', 'biomasa_disponible_display')

    @admin.display(description='Biomasa Actual (kg)')
    def biomasa_actual_display(self, obj):
        return f"{obj.biomasa_actual:.2f} kg"

    @admin.display(description='Biomasa Disponible (kg)')
    def biomasa_disponible_display(self, obj):
        return f"{obj.biomasa_disponible:.2f} kg"


# ================================================================
# REGISTRO DE LOTES
# ================================================================

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_lote', 'etapa_actual', 'cantidad_total_peces', 
        'peso_promedio_pez_gr', 'biomasa_kg_display', 'ubicacion_actual', 
        'fecha_ingreso_etapa'
    )
    list_filter = ('etapa_actual', 'activo')
    search_fields = ('codigo_lote',)
    readonly_fields = (
        'codigo_lote', 'biomasa_kg_display', 'ubicacion_actual', 
        'cantidad_inicial', 'peso_promedio_inicial_gr',
    )
    fieldsets = (
        (None, {
            'fields': ('codigo_lote', 'etapa_actual', 'activo', 'fecha_ingreso_etapa')
        }),
        ('Detalles del Lote', {
            'fields': ('cantidad_total_peces', 'peso_promedio_pez_gr', 
                       'talla_min_cm', 'talla_max_cm')
        }),
        ('Cálculos Automáticos', {
            'fields': ('biomasa_kg_display', 'cantidad_inicial', 'peso_promedio_inicial_gr')
        }),
        ('Ubicación', {
            'fields': ('bastidor', 'artesa', 'jaula')
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('bastidor', 'artesa', 'jaula')

    @admin.display(description='Ubicación Actual')
    def ubicacion_actual(self, obj):
        if obj.bastidor:
            return f"Bastidor: {obj.bastidor.codigo}"
        if obj.artesa:
            return f"Artesa: {obj.artesa.codigo}"
        if obj.jaula:
            return f"Jaula: {obj.jaula.codigo}"
        return "Sin asignar"
    
    @admin.display(description='Biomasa (kg)')
    def biomasa_kg_display(self, obj):
        return f"{obj.biomasa_kg:.2f} kg"

    # --- Acciones mejoradas (ahora avanzan la fecha) ---
    @admin.action(description='Avanzar fecha de ingreso 1 día')
    def avanzar_un_dia(self, request, queryset):
        for lote in queryset:
            lote.fecha_ingreso_etapa += timezone.timedelta(days=1)
            lote.save()
        self.message_user(request, "Se avanzó la fecha de los lotes seleccionados en 1 día.")

    @admin.action(description='Avanzar fecha de ingreso 7 días')
    def avanzar_siete_dias(self, request, queryset):
        for lote in queryset:
            lote.fecha_ingreso_etapa += timezone.timedelta(days=7)
            lote.save()
        self.message_user(request, "Se avanzó la fecha de los lotes seleccionados en 7 días.")


# ================================================================
# REGISTRO DE EVENTOS
# ================================================================

@admin.register(RegistroDiario)
class RegistroDiarioAdmin(admin.ModelAdmin):
    list_display = ('lote', 'fecha', 'alimentacion_realizada', 'limpieza_realizada')
    list_filter = ('fecha', 'alimentacion_realizada', 'limpieza_realizada')
    search_fields = ('lote__codigo_lote',)
    list_select_related = ('lote',)

@admin.register(RegistroMortalidad)
class RegistroMortalidadAdmin(admin.ModelAdmin):
    list_display = ('lote', 'fecha', 'cantidad', 'registrado_por')
    list_filter = ('fecha',)
    search_fields = ('lote__codigo_lote', 'registrado_por__username')
    list_select_related = ('lote', 'registrado_por')

@admin.register(HistorialMovimiento)
class HistorialMovimientoAdmin(admin.ModelAdmin):
    list_display = ('lote', 'fecha', 'tipo_movimiento', 'descripcion', 'cantidad_afectada')
    list_filter = ('tipo_movimiento',)
    search_fields = ('lote__codigo_lote', 'descripcion')
    list_select_related = ('lote',)
    readonly_fields = ('lote', 'fecha', 'tipo_movimiento', 'descripcion', 'cantidad_afectada')

@admin.register(RegistroUnidad)
class RegistroUnidadAdmin(admin.ModelAdmin):
    list_display = ('unidad', 'fecha', 'biomasa_kg', 'cantidad_peces', 'alimento_kg', 'mortalidad_total')
    list_filter = ('fecha',)
    readonly_fields = ('unidad', 'fecha', 'biomasa_kg', 'cantidad_peces', 'alimento_kg', 'mortalidad_total')

@admin.register(Enfermedad)
class EnfermedadAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)