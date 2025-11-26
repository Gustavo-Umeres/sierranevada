from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from produccion.models import Lote


class Cliente(models.Model):
    TIPOS_CLIENTE = (
        ("MAYORISTA", "Mayorista"),
        ("MINORISTA", "Minorista"),
    )

    nombre = models.CharField(max_length=255)
    ruc_dni = models.CharField(max_length=15, unique=True, verbose_name="RUC / DNI")
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    tipo_cliente = models.CharField(max_length=15, choices=TIPOS_CLIENTE, default="MAYORISTA")

    def __str__(self):
        return f"{self.nombre} - {self.ruc_dni}"


class TipoVenta(models.TextChoices):
    MAYORISTA = "MAYORISTA", "Mayorista"
    MINORISTA_POS = "MINORISTA_POS", "Minorista - Punto de Venta"
    MINORISTA_PEDIDO = "MINORISTA_PEDIDO", "Minorista - Pedido"


class PedidoMayorista(models.Model):
    ESTADOS = (
        ("PENDIENTE", "Pendiente"),
        ("APROBADO", "Aprobado"),
        ("RECHAZADO", "Rechazado"),
        ("DESPACHADO", "Despachado"),
    )

    codigo = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="pedidos_mayoristas")
    lote = models.ForeignKey(
        Lote,
        on_delete=models.PROTECT,
        limit_choices_to={"etapa_actual": "ENGORDE", "activo": True},
        related_name="pedidos_mayoristas",
        verbose_name="Lote (Engorde)",
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    toneladas_solicitadas = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Toneladas solicitadas"
    )
    precio_unitario_ton = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio por tonelada (S/.)"
    )
    total_venta = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), editable=False)
    estado = models.CharField(max_length=15, choices=ESTADOS, default="PENDIENTE")
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_mayoristas_aprobados",
    )
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    observaciones_aprobacion = models.TextField(blank=True, null=True)

    tipo_venta = models.CharField(
        max_length=20, choices=TipoVenta.choices, default=TipoVenta.MAYORISTA, editable=False
    )

    def __str__(self):
        return self.codigo

    def save(self, *args, **kwargs):
        if not self.pk and not self.codigo:
            prefijo = "PM"
            now = timezone.now()
            year_month = now.strftime("%y%m")
            ultimo = PedidoMayorista.objects.filter(codigo__startswith=f"{prefijo}{year_month}").order_by(
                "codigo"
            ).last()
            correlativo = int(ultimo.codigo.split("-")[-1]) + 1 if ultimo else 1
            self.codigo = f"{prefijo}{year_month}-{correlativo:03d}"

        self.total_venta = self.toneladas_solicitadas * self.precio_unitario_ton
        super().save(*args, **kwargs)


class DetallePedidoMayorista(models.Model):
    pedido = models.ForeignKey(PedidoMayorista, on_delete=models.CASCADE, related_name="detalles")
    descripcion = models.CharField(max_length=255, verbose_name="Descripción del producto")
    cantidad_ton = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad (ton)")
    precio_unitario_ton = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio unitario (S/.)")

    @property
    def subtotal(self):
        return self.cantidad_ton * self.precio_unitario_ton

    def __str__(self):
        return f"{self.descripcion} - {self.cantidad_ton} ton"


class VentaMinoristaBase(models.Model):
    TIPOS_PAGO = (
        ("EFECTIVO", "Efectivo"),
        ("TARJETA", "Tarjeta"),
        ("TRANSFERENCIA", "Transferencia"),
    )

    # No usamos related_name explícito aquí para evitar choques entre subclases;
    # Django creará <modelo>_set para cada clase concreta.
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    lote = models.ForeignKey(
        Lote,
        on_delete=models.PROTECT,
        limit_choices_to={"etapa_actual": "ENGORDE", "activo": True},
        verbose_name="Lote (Engorde)",
    )
    fecha = models.DateField(default=timezone.now)
    total_venta = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), editable=False)
    tipo_pago = models.CharField(max_length=15, choices=TIPOS_PAGO, default="EFECTIVO")
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class VentaMinoristaPOS(VentaMinoristaBase):
    codigo = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    tipo_venta = models.CharField(
        max_length=20, choices=TipoVenta.choices, default=TipoVenta.MINORISTA_POS, editable=False
    )

    def __str__(self):
        return self.codigo

    def save(self, *args, **kwargs):
        if not self.pk and not self.codigo:
            prefijo = "VP"
            now = timezone.now()
            year_month = now.strftime("%y%m")
            ultimo = VentaMinoristaPOS.objects.filter(codigo__startswith=f"{prefijo}{year_month}").order_by(
                "codigo"
            ).last()
            correlativo = int(ultimo.codigo.split("-")[-1]) + 1 if ultimo else 1
            self.codigo = f"{prefijo}{year_month}-{correlativo:04d}"
        super().save(*args, **kwargs)


class DetalleVentaPOS(models.Model):
    venta = models.ForeignKey(VentaMinoristaPOS, on_delete=models.CASCADE, related_name="detalles")
    descripcion = models.CharField(max_length=255)
    cantidad_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad (kg)")
    precio_unitario_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio unitario (S/.)")

    @property
    def subtotal(self):
        return self.cantidad_kg * self.precio_unitario_kg

    def __str__(self):
        return f"{self.descripcion} - {self.cantidad_kg} kg"


class VentaMinoristaPedido(VentaMinoristaBase):
    ESTADOS = (
        ("REGISTRADO", "Registrado"),
        ("PREPARADO", "Preparado"),
        ("ENTREGADO", "Entregado"),
        ("CANCELADO", "Cancelado"),
    )

    codigo = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    fecha_pedido = models.DateField(default=timezone.now)
    fecha_entrega = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default="REGISTRADO")
    tipo_venta = models.CharField(
        max_length=20, choices=TipoVenta.choices, default=TipoVenta.MINORISTA_PEDIDO, editable=False
    )

    def __str__(self):
        return self.codigo

    def save(self, *args, **kwargs):
        if not self.pk and not self.codigo:
            prefijo = "VR"
            now = timezone.now()
            year_month = now.strftime("%y%m")
            ultimo = VentaMinoristaPedido.objects.filter(codigo__startswith=f"{prefijo}{year_month}").order_by(
                "codigo"
            ).last()
            correlativo = int(ultimo.codigo.split("-")[-1]) + 1 if ultimo else 1
            self.codigo = f"{prefijo}{year_month}-{correlativo:04d}"
        super().save(*args, **kwargs)


class DetalleVentaPedido(models.Model):
    venta = models.ForeignKey(VentaMinoristaPedido, on_delete=models.CASCADE, related_name="detalles")
    descripcion = models.CharField(max_length=255)
    cantidad_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad (kg)")
    precio_unitario_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio unitario (S/.)")

    @property
    def subtotal(self):
        return self.cantidad_kg * self.precio_unitario_kg

    def __str__(self):
        return f"{self.descripcion} - {self.cantidad_kg} kg"


class RegistroVenta(models.Model):
    """
    Registro consolidado de ventas para reportes por tipo de venta.
    """

    fecha = models.DateField(default=timezone.now)
    tipo_venta = models.CharField(max_length=20, choices=TipoVenta.choices)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True)
    total_kg = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_monto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.fecha} - {self.get_tipo_venta_display()} - {self.total_monto}"


def descontar_biomasa_lote(lote: Lote, kilos_vendidos: Decimal):
    """
    Descuenta biomasa y cantidad de peces de un lote de engorde según venta en kg.
    Se asume peso_promedio_pez_gr definido.
    """
    if not lote.peso_promedio_pez_gr or lote.peso_promedio_pez_gr <= 0:
        return

    if kilos_vendidos <= 0:
        return

    with transaction.atomic():
        lote.refresh_from_db()
        peso_unitario_kg = lote.peso_promedio_pez_gr / Decimal(1000)
        if peso_unitario_kg <= 0:
            return

        peces_a_descontar = (kilos_vendidos / peso_unitario_kg).quantize(Decimal("1."), rounding="ROUND_HALF_UP")
        if peces_a_descontar > lote.cantidad_total_peces:
            peces_a_descontar = Decimal(lote.cantidad_total_peces)

        lote.cantidad_total_peces = lote.cantidad_total_peces - int(peces_a_descontar)
        if lote.cantidad_total_peces <= 0:
            lote.cantidad_total_peces = 0
            lote.activo = False
        lote.save()

