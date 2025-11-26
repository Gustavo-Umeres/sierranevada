from django.contrib import admin

from .models import (
    Cliente,
    PedidoMayorista,
    DetallePedidoMayorista,
    VentaMinoristaPOS,
    DetalleVentaPOS,
    VentaMinoristaPedido,
    DetalleVentaPedido,
    RegistroVenta,
)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ruc_dni", "tipo_cliente", "telefono", "email")
    search_fields = ("nombre", "ruc_dni")


class DetallePedidoMayoristaInline(admin.TabularInline):
    model = DetallePedidoMayorista
    extra = 0


@admin.register(PedidoMayorista)
class PedidoMayoristaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "cliente", "lote", "toneladas_solicitadas", "total_venta", "estado", "fecha_creacion")
    list_filter = ("estado", "fecha_creacion")
    search_fields = ("codigo", "cliente__nombre", "lote__codigo_lote")
    inlines = [DetallePedidoMayoristaInline]


class DetalleVentaPOSInline(admin.TabularInline):
    model = DetalleVentaPOS
    extra = 0


@admin.register(VentaMinoristaPOS)
class VentaMinoristaPOSAdmin(admin.ModelAdmin):
    list_display = ("codigo", "cliente", "lote", "fecha", "total_venta", "tipo_pago")
    list_filter = ("tipo_pago", "fecha")
    search_fields = ("codigo", "cliente__nombre", "lote__codigo_lote")
    inlines = [DetalleVentaPOSInline]


class DetalleVentaPedidoInline(admin.TabularInline):
    model = DetalleVentaPedido
    extra = 0


@admin.register(VentaMinoristaPedido)
class VentaMinoristaPedidoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "cliente", "lote", "fecha_pedido", "estado", "total_venta")
    list_filter = ("estado", "fecha_pedido")
    search_fields = ("codigo", "cliente__nombre", "lote__codigo_lote")
    inlines = [DetalleVentaPedidoInline]


@admin.register(RegistroVenta)
class RegistroVentaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "tipo_venta", "cliente", "lote", "total_kg", "total_monto")
    list_filter = ("tipo_venta", "fecha")
    search_fields = ("cliente__nombre", "lote__codigo_lote")

