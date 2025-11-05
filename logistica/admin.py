from django.contrib import admin
from .models import Proveedor, CategoriaInsumo, Insumo, OrdenCompra, DetalleOrdenCompra, MovimientoInventario

class DetalleOrdenCompraInline(admin.TabularInline):
    model = DetalleOrdenCompra
    extra = 1
    raw_id_fields = ['insumo']

@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ('codigo_orden', 'proveedor', 'fecha_creacion', 'fecha_esperada_entrega', 'estado', 'total_costo', 'creado_por')
    list_filter = ('estado', 'fecha_creacion', 'proveedor')
    search_fields = ('codigo_orden', 'proveedor__nombre')
    inlines = [DetalleOrdenCompraInline]
    readonly_fields = ('total_costo', 'creado_por', 'codigo_orden')

@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'stock_actual', 'unidad_medida', 'stock_minimo')
    list_filter = ('categoria',)
    search_fields = ('nombre',)
    readonly_fields = ('stock_actual',) 

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'insumo', 'tipo_movimiento', 'cantidad', 'usuario')
    list_filter = ('tipo_movimiento', 'fecha')
    search_fields = ('insumo__nombre', 'descripcion')
    raw_id_fields = ['insumo', 'usuario']

admin.site.register(Proveedor)
admin.site.register(CategoriaInsumo)