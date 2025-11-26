from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from produccion.models import Lote

from .forms import (
    ClienteForm,
    PedidoMayoristaForm,
    PedidoMayoristaAprobacionForm,
    DetallePedidoMayoristaFormSet,
    VentaMinoristaPOSForm,
    DetalleVentaPOSFormSet,
    VentaMinoristaPedidoForm,
    DetalleVentaPedidoFormSet,
)
from .models import (
    Cliente,
    PedidoMayorista,
    VentaMinoristaPOS,
    VentaMinoristaPedido,
    RegistroVenta,
    descontar_biomasa_lote,
    TipoVenta,
)


class ComercializacionPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restringe acceso a usuarios del grupo Comercializacion o staff."""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name="Comercializacion").exists()


@login_required
def dashboard_comercializacion(request):
    total_mayorista = (
        RegistroVenta.objects.filter(tipo_venta=TipoVenta.MAYORISTA).aggregate(total=Sum("total_monto"))["total"]
        or Decimal("0.00")
    )
    total_pos = (
        RegistroVenta.objects.filter(tipo_venta=TipoVenta.MINORISTA_POS).aggregate(total=Sum("total_monto"))["total"]
        or Decimal("0.00")
    )
    total_pedidos = (
        RegistroVenta.objects.filter(tipo_venta=TipoVenta.MINORISTA_PEDIDO).aggregate(total=Sum("total_monto"))[
            "total"
        ]
        or Decimal("0.00")
    )

    context = {
        "total_mayorista": total_mayorista,
        "total_pos": total_pos,
        "total_pedidos": total_pedidos,
    }
    return render(request, "comercializacion/dashboard.html", context)


# ================================================================
# CLIENTES
# ================================================================


class ClienteListView(ComercializacionPermissionMixin, ListView):
    model = Cliente
    template_name = "comercializacion/cliente_list.html"
    context_object_name = "clientes"


class ClienteCreateView(ComercializacionPermissionMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "comercializacion/cliente_form.html"
    success_url = reverse_lazy("cliente-list")
    extra_context = {"titulo": "Registrar cliente"}


class ClienteUpdateView(ComercializacionPermissionMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "comercializacion/cliente_form.html"
    success_url = reverse_lazy("cliente-list")
    extra_context = {"titulo": "Editar cliente"}


# ================================================================
# 1. PEDIDO MAYORISTA POR TONELAJE
# ================================================================


class PedidoMayoristaListView(ComercializacionPermissionMixin, ListView):
    model = PedidoMayorista
    template_name = "comercializacion/pedido_mayorista_list.html"
    context_object_name = "pedidos"
    paginate_by = 20
    ordering = ["-fecha_creacion"]


class PedidoMayoristaCreateView(ComercializacionPermissionMixin, CreateView):
    model = PedidoMayorista
    form_class = PedidoMayoristaForm
    template_name = "comercializacion/pedido_mayorista_form.html"
    success_url = reverse_lazy("pedido-mayorista-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo Pedido Mayorista por Tonelaje"
        if "detalle_formset" not in context:
            context["detalle_formset"] = DetallePedidoMayoristaFormSet(
                self.request.POST or None, prefix="detalles"
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalle_formset = context["detalle_formset"]
        with transaction.atomic():
            self.object = form.save()
            if detalle_formset.is_valid():
                detalle_formset.instance = self.object
                detalles = detalle_formset.save()
                total_detalles = sum(d.subtotal for d in detalles)
                if total_detalles > 0:
                    self.object.total_venta = total_detalles
                    self.object.save()
                messages.success(self.request, "Pedido mayorista registrado correctamente.")
                return super().form_valid(form)
            return self.form_invalid(form)


class PedidoMayoristaDetailView(ComercializacionPermissionMixin, DetailView):
    model = PedidoMayorista
    template_name = "comercializacion/pedido_mayorista_detail.html"
    context_object_name = "pedido"


class PedidoMayoristaAprobarView(ComercializacionPermissionMixin, UpdateView):
    model = PedidoMayorista
    form_class = PedidoMayoristaAprobacionForm
    template_name = "comercializacion/pedido_mayorista_aprobar.html"
    success_url = reverse_lazy("pedido-mayorista-list")

    def form_valid(self, form):
        pedido = form.save(commit=False)
        if pedido.estado == "APROBADO":
            # Validar biomasa disponible en el lote
            lote = pedido.lote
            toneladas_disponibles = (lote.biomasa_kg / Decimal(1000)).quantize(Decimal("0.01"))
            if pedido.toneladas_solicitadas > toneladas_disponibles:
                messages.error(
                    self.request,
                    f"El lote {lote.codigo_lote} solo tiene {toneladas_disponibles} ton disponibles.",
                )
                return self.form_invalid(form)

            pedido.aprobado_por = self.request.user
            pedido.fecha_aprobacion = timezone.now()

        pedido.save()
        messages.success(self.request, f"Pedido {pedido.codigo} actualizado a estado {pedido.get_estado_display()}.")
        return super().form_valid(form)


@login_required
@transaction.atomic
def despachar_pedido_mayorista(request, pk):
    pedido = get_object_or_404(PedidoMayorista, pk=pk)
    if pedido.estado != "APROBADO":
        messages.warning(request, "Solo se pueden despachar pedidos en estado APROBADO.")
        return redirect("pedido-mayorista-detail", pk=pk)

    toneladas = pedido.toneladas_solicitadas
    kilos = toneladas * Decimal("1000")
    descontar_biomasa_lote(pedido.lote, kilos)

    RegistroVenta.objects.create(
        fecha=pedido.fecha_creacion.date(),
        tipo_venta=TipoVenta.MAYORISTA,
        cliente=pedido.cliente,
        lote=pedido.lote,
        total_kg=kilos,
        total_monto=pedido.total_venta,
    )

    pedido.estado = "DESPACHADO"
    pedido.save(update_fields=["estado"])
    messages.success(request, f"Pedido {pedido.codigo} despachado correctamente.")
    return redirect("pedido-mayorista-detail", pk=pk)


# ================================================================
# 3. VENTA AL POR MENOR - PUNTO DE VENTA
# ================================================================


class VentaPOSListView(ComercializacionPermissionMixin, ListView):
    model = VentaMinoristaPOS
    template_name = "comercializacion/venta_pos_list.html"
    context_object_name = "ventas"
    paginate_by = 20
    ordering = ["-fecha"]


class VentaPOSCreateView(ComercializacionPermissionMixin, CreateView):
    model = VentaMinoristaPOS
    form_class = VentaMinoristaPOSForm
    template_name = "comercializacion/venta_pos_form.html"
    success_url = reverse_lazy("venta-pos-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Venta al por menor - Punto de Venta"
        if "detalle_formset" not in context:
            context["detalle_formset"] = DetalleVentaPOSFormSet(self.request.POST or None, prefix="detalles")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalle_formset = context["detalle_formset"]
        with transaction.atomic():
            form.instance.creado_por = self.request.user
            self.object = form.save()
            if detalle_formset.is_valid():
                detalle_formset.instance = self.object
                detalles = detalle_formset.save()
                total_kg = sum(d.cantidad_kg for d in detalles)
                total_monto = sum(d.subtotal for d in detalles)
                self.object.total_venta = total_monto
                self.object.save()

                descontar_biomasa_lote(self.object.lote, total_kg)

                RegistroVenta.objects.create(
                    fecha=self.object.fecha,
                    tipo_venta=TipoVenta.MINORISTA_POS,
                    cliente=self.object.cliente,
                    lote=self.object.lote,
                    total_kg=total_kg,
                    total_monto=total_monto,
                )

                messages.success(self.request, "Venta en Punto de Venta registrada correctamente.")
                return super().form_valid(form)
            return self.form_invalid(form)


class VentaPOSDetailView(ComercializacionPermissionMixin, DetailView):
    model = VentaMinoristaPOS
    template_name = "comercializacion/venta_pos_detail.html"
    context_object_name = "venta"


# ================================================================
# 4. VENTA AL POR MENOR - POR PEDIDOS
# ================================================================


class VentaPedidoListView(ComercializacionPermissionMixin, ListView):
    model = VentaMinoristaPedido
    template_name = "comercializacion/venta_pedido_list.html"
    context_object_name = "pedidos"
    paginate_by = 20
    ordering = ["-fecha_pedido"]


class VentaPedidoCreateView(ComercializacionPermissionMixin, CreateView):
    model = VentaMinoristaPedido
    form_class = VentaMinoristaPedidoForm
    template_name = "comercializacion/venta_pedido_form.html"
    success_url = reverse_lazy("venta-pedido-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Venta al por menor - Pedido"
        if "detalle_formset" not in context:
            context["detalle_formset"] = DetalleVentaPedidoFormSet(self.request.POST or None, prefix="detalles")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalle_formset = context["detalle_formset"]
        with transaction.atomic():
            form.instance.creado_por = self.request.user
            self.object = form.save()
            if detalle_formset.is_valid():
                detalle_formset.instance = self.object
                detalles = detalle_formset.save()
                total_kg = sum(d.cantidad_kg for d in detalles)
                total_monto = sum(d.subtotal for d in detalles)
                self.object.total_venta = total_monto
                self.object.save()

                RegistroVenta.objects.create(
                    fecha=self.object.fecha_pedido,
                    tipo_venta=TipoVenta.MINORISTA_PEDIDO,
                    cliente=self.object.cliente,
                    lote=self.object.lote,
                    total_kg=total_kg,
                    total_monto=total_monto,
                )

                messages.success(self.request, "Pedido minorista registrado correctamente.")
                return super().form_valid(form)
            return self.form_invalid(form)


class VentaPedidoDetailView(ComercializacionPermissionMixin, DetailView):
    model = VentaMinoristaPedido
    template_name = "comercializacion/venta_pedido_detail.html"
    context_object_name = "pedido"


@login_required
@transaction.atomic
def marcar_pedido_entregado(request, pk):
    venta = get_object_or_404(VentaMinoristaPedido, pk=pk)
    if venta.estado != "PREPARADO":
        messages.warning(self.request, "Solo se pueden marcar como ENTREGADOS los pedidos PREPARADOS.")
        return redirect("venta-pedido-detail", pk=pk)
    venta.estado = "ENTREGADO"
    venta.fecha_entrega = timezone.now().date()
    venta.save(update_fields=["estado", "fecha_entrega"])
    messages.success(request, f"Pedido {venta.codigo} marcado como ENTREGADO.")
    return redirect("venta-pedido-detail", pk=pk)


# ================================================================
# 5. REPORTE DE VENTAS POR TIPO DE VENTA
# ================================================================


@login_required
def reporte_ventas_view(request):
    tipo = request.GET.get("tipo_venta")
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")

    ventas = RegistroVenta.objects.all()
    if tipo:
        ventas = ventas.filter(tipo_venta=tipo)
    if fecha_desde:
        ventas = ventas.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        ventas = ventas.filter(fecha__lte=fecha_hasta)

    resumen_por_tipo = (
        RegistroVenta.objects.values("tipo_venta")
        .annotate(total_monto=Sum("total_monto"), total_kg=Sum("total_kg"), cantidad=Sum(1 * F("id") / F("id")))
        .order_by("tipo_venta")
    )

    context = {
        "ventas": ventas,
        "tipo_seleccionado": tipo,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "tipos_venta": TipoVenta.choices,
        "resumen_por_tipo": resumen_por_tipo,
    }
    return render(request, "comercializacion/reporte_ventas.html", context)
