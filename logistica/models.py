from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver

# ================================================================
# ACTIVIDAD 3: REGISTRAR PROVEEDORES
# ================================================================
class Proveedor(models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre o Razón Social")
    ruc = models.CharField(max_length=11, unique=True, verbose_name="RUC")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")

    def __str__(self):
        return self.nombre


# ================================================================
# ACTIVIDAD 2: REPORTAR STOCKS (Modelos de Insumos)
# ================================================================
class CategoriaInsumo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Insumo(models.Model):
    UNIDADES_MEDIDA = (
        ('kg', 'Kilogramos'),
        ('lt', 'Litros'),
        ('un', 'Unidades'),
        ('m3', 'Metros Cúbicos'),
    )

    nombre = models.CharField(max_length=255, unique=True, help_text="Ej: 'Alevines 1', 'Crecimiento 2', 'Oxígeno', 'Vacuna X'")
    categoria = models.ForeignKey(CategoriaInsumo, on_delete=models.SET_NULL, null=True, related_name="insumos")
    unidad_medida = models.CharField(max_length=3, choices=UNIDADES_MEDIDA, default='kg')
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('100.00'), help_text="Stock mínimo para generar alertas")

    def __str__(self):
        return f"{self.nombre} ({self.stock_actual} {self.get_unidad_medida_display()})"

    class Meta:
        ordering = ['categoria', 'nombre']


# ================================================================
# ACTIVIDAD 4: GENERAR ÓRDENES DE COMPRAS
# ================================================================
class OrdenCompra(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECIBIDA', 'Recibida'),
        ('CANCELADA', 'Cancelada'),
    )

    codigo_orden = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="ordenes_compra")
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Creación")
    fecha_esperada_entrega = models.DateField(verbose_name="Fecha Esperada de Entrega")
    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ordenes_creadas")
    total_costo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)

    def __str__(self):
        return self.codigo_orden

    def save(self, *args, **kwargs):
        if not self.pk:
            prefijo = 'OC'
            now = timezone.now()
            year_month = now.strftime('%y%m')
            ultimo = OrdenCompra.objects.filter(codigo_orden__startswith=f'{prefijo}{year_month}').order_by('codigo_orden').last()
            correlativo = int(ultimo.codigo_orden.split('-')[-1]) + 1 if ultimo else 1
            self.codigo_orden = f'{prefijo}{year_month}-{correlativo:03d}'

        # Recalcular total si no se está recibiendo
        if self.pk and self.estado != 'RECIBIDA':
            self.total_costo = self.detalles.aggregate(
                total=Coalesce(Sum(F('cantidad') * F('precio_unitario')), Decimal('0.00'))
            )['total']

        super().save(*args, **kwargs)

    def marcar_como_recibida(self):
        """Recibir la orden y actualizar inventario."""
        if self.estado != 'RECIBIDA':
            with transaction.atomic():
                for detalle in self.detalles.all():
                    MovimientoInventario.objects.create(
                        insumo=detalle.insumo,
                        tipo_movimiento='ENTRADA',
                        cantidad=detalle.cantidad,
                        usuario=self.creado_por,
                        descripcion=f"Entrada automática por OC: {self.codigo_orden}"
                    )
                self.estado = 'RECIBIDA'
                self.save()


class DetalleOrdenCompra(models.Model):
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name="detalles")
    insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario (Sin IGV)")

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} de {self.insumo.nombre}"


# ================================================================
# ACTIVIDAD 1: REGISTRAR ENTRADAS Y SALIDAS
# ================================================================
class MovimientoInventario(models.Model):
    TIPOS_MOVIMIENTO = (
        ('ENTRADA', 'Entrada (Compra/Ingreso)'),
        ('SALIDA', 'Salida (Producción/Baja)'),
        ('AJUSTE_POS', 'Ajuste Positivo (Sobrante)'),
        ('AJUSTE_NEG', 'Ajuste Negativo (Pérdida/Merma)'),
    )

    insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT, related_name="movimientos")
    tipo_movimiento = models.CharField(max_length=10, choices=TIPOS_MOVIMIENTO)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, help_text="Siempre un número positivo")
    fecha = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción o Justificación")

    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} de {self.cantidad} {self.insumo.unidad_medida} de {self.insumo.nombre}"

    class Meta:
        ordering = ['-fecha']
