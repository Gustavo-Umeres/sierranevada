from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_POST


import openpyxl
from django.http import HttpResponse
from django.db.models import Q


from .models import Proveedor, Insumo, CategoriaInsumo, OrdenCompra, DetalleOrdenCompra, MovimientoInventario
from .forms import ProveedorForm, InsumoForm, CategoriaInsumoForm, OrdenCompraForm, DetalleOrdenCompraFormSet, MovimientoManualForm

# ... (al inicio de logistica/views.py, con las otras importaciones)
from django.http import JsonResponse
from django.db.models.functions import TruncDay
from datetime import datetime, timedelta
from decimal import Decimal
import calendar

# Importar el modelo Lote de PRODUCCION para leer la demanda
try:
    from produccion.models import Lote
except ImportError:
    Lote = None  # Manejar error si la app no existe

# ================================================================
# MIXIN DE PERMISOS
# ================================================================
class LogisticaPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Asegura que el usuario pertenezca al grupo 'Logistica' o sea staff."""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='Logistica').exists()

# ================================================================
# DASHBOARD
# ================================================================
@login_required
def dashboard_logistica(request):
    alertas_stock = Insumo.objects.filter(stock_actual__lt=F('stock_minimo'))
    ordenes_pendientes = OrdenCompra.objects.filter(estado__in=['PENDIENTE', 'APROBADA']).count()
    context = {'alertas_stock': alertas_stock, 'ordenes_pendientes': ordenes_pendientes}
    return render(request, 'logistica/dashboard.html', context)

# ================================================================
# ACTIVIDAD 2: VISTA DE INVENTARIO
# ================================================================
class InsumoListView(LogisticaPermissionMixin, ListView):
    model = Insumo
    template_name = 'logistica/insumo_list.html'
    context_object_name = 'insumos'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaInsumo.objects.all()
        return context

class InsumoCreateView(LogisticaPermissionMixin, CreateView):
    model = Insumo
    form_class = InsumoForm
    template_name = 'logistica/insumo_form.html'
    success_url = reverse_lazy('inventario-list')
    extra_context = {'titulo': 'Crear Nuevo Insumo'}

class InsumoUpdateView(LogisticaPermissionMixin, UpdateView):
    model = Insumo
    form_class = InsumoForm
    template_name = 'logistica/insumo_form.html'
    success_url = reverse_lazy('inventario-list')
    extra_context = {'titulo': 'Editar Insumo'}

# ================================================================
# ACTIVIDAD 3: PROVEEDORES
# ================================================================
class ProveedorListView(LogisticaPermissionMixin, ListView):
    model = Proveedor
    template_name = 'logistica/proveedor_list.html'
    context_object_name = 'proveedores'
    paginate_by = 20

    def get_queryset(self):
        return Proveedor.objects.all().order_by('-estado', 'nombre')


@login_required
@require_POST
def toggle_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    proveedor.estado = not proveedor.estado
    proveedor.save()
    estado_txt = "activado" if proveedor.estado else "desactivado"
    messages.success(request, f"Proveedor {proveedor.nombre} {estado_txt}.")
    return redirect('proveedor-list')  # ajusta si tu name es diferente
# def toggle_proveedor(request, pk):
#     proveedor = get_object_or_404(Proveedor, pk=pk)
#     proveedor.estado = not proveedor.estado   
#     proveedor.save()
#     return redirect('proveedor-list')

class ProveedorCreateView(LogisticaPermissionMixin, CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'logistica/proveedor_form.html'
    success_url = reverse_lazy('proveedor-list')
    extra_context = {'titulo': 'Registrar Proveedor'}

class ProveedorUpdateView(LogisticaPermissionMixin, UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'logistica/proveedor_form.html'
    success_url = reverse_lazy('proveedor-list')
    extra_context = {'titulo': 'Editar Proveedor'}

# class ProveedorDeleteView(LogisticaPermissionMixin, DeleteView):
#     model = Proveedor
#     template_name = 'logistica/confirm_delete.html'
#     success_url = reverse_lazy('proveedor-list')

class ProveedorDarDeBajaView(View):

    success_url = reverse_lazy('proveedor-list') 
    template_name = 'logistica/confirm_delete.html'

    def get(self, request, pk):
        proveedor = get_object_or_404(Proveedor, pk=pk)
        return render(request, self.template_name, {'object': proveedor, 'action_name': 'Dar de Baja'}) 

    def post(self, request, pk):
        """Procesa la confirmación y establece el proveedor como inactivo."""
        proveedor = get_object_or_404(Proveedor, pk=pk)
        
        # Lógica de dar de baja:
        # 1. Verificar si el proveedor ya tiene el campo 'activo' (del paso anterior).
        if hasattr(proveedor, 'activo'):
            proveedor.activo = False
            proveedor.save()
        
        # 2. Redirigir al usuario.
        return redirect(self.success_url)

# ================================================================
# ACTIVIDAD 4: ÓRDENES DE COMPRA
# ================================================================
class OrdenCompraListView(LogisticaPermissionMixin, ListView):
    model = OrdenCompra
    template_name = 'logistica/ordencompra_list.html'
    context_object_name = 'ordenes'
    paginate_by = 20
    ordering = ['-fecha_creacion']

class OrdenCompraCreateView(LogisticaPermissionMixin, CreateView):
    model = OrdenCompra
    form_class = OrdenCompraForm
    template_name = 'logistica/ordencompra_form.html'
    success_url = reverse_lazy('ordencompra-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Orden de Compra'
        context['detalle_formset'] = DetalleOrdenCompraFormSet(self.request.POST or None, prefix='detalles')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalle_formset = context['detalle_formset']
        with transaction.atomic():
            form.instance.creado_por = self.request.user
            self.object = form.save()
            if detalle_formset.is_valid():
                detalle_formset.instance = self.object
                detalle_formset.save()
                self.object.save()
                messages.success(self.request, "Orden de Compra creada exitosamente.")
                return super().form_valid(form)
            return self.form_invalid(form)

class OrdenCompraUpdateView(LogisticaPermissionMixin, UpdateView):
    model = OrdenCompra
    form_class = OrdenCompraForm
    template_name = 'logistica/ordencompra_form.html'
    success_url = reverse_lazy('ordencompra-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f"Editar Orden {self.object.codigo_orden}"
        context['detalle_formset'] = DetalleOrdenCompraFormSet(
            self.request.POST or None, instance=self.object, prefix='detalles'
        )
        if self.object.estado == 'RECIBIDA':
            for form in context['detalle_formset']:
                form.fields['insumo'].disabled = True
                form.fields['cantidad'].disabled = True
                form.fields['precio_unitario'].disabled = True
        return context

    def form_valid(self, form):
        if self.object.estado == 'RECIBIDA':
            messages.error(self.request, "No se puede modificar una orden que ya ha sido RECIBIDA.")
            return self.form_invalid(form)
        context = self.get_context_data()
        detalle_formset = context['detalle_formset']
        with transaction.atomic():
            self.object = form.save()
            if detalle_formset.is_valid():
                detalle_formset.save()
                self.object.save()
                messages.success(self.request, "Orden de Compra actualizada exitosamente.")
                return super().form_valid(form)
            return self.form_invalid(form)

class OrdenCompraDetailView(LogisticaPermissionMixin, DetailView):
    model = OrdenCompra
    template_name = 'logistica/ordencompra_detail.html'
    context_object_name = 'orden'

@login_required
@transaction.atomic
def recibir_orden_compra(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)
    if request.method == 'POST':
        if orden.estado != 'RECIBIDA':
            for detalle in orden.detalles.all():
                MovimientoInventario.objects.create(
                    insumo=detalle.insumo,
                    tipo_movimiento='ENTRADA',
                    cantidad=detalle.cantidad,
                    usuario=request.user,
                    descripcion=f"Entrada automática por OC: {orden.codigo_orden}"
                )
            orden.estado = 'RECIBIDA'
            orden.save(update_fields=['estado'])
            messages.success(request, f"Orden {orden.codigo_orden} marcada como RECIBIDA.")
        else:
            messages.warning(request, f"La orden {orden.codigo_orden} ya había sido recibida.")
        return redirect('ordencompra-detail', pk=pk)
    return redirect('ordencompra-list')

# ================================================================
# MOVIMIENTOS
# ================================================================
class MovimientoInventarioListView(LogisticaPermissionMixin, ListView):
    model = MovimientoInventario
    template_name = 'logistica/movimiento_list.html'
    context_object_name = 'movimientos'
    paginate_by = 50
    ordering = ['-fecha']

class MovimientoManualCreateView(LogisticaPermissionMixin, CreateView):
    model = MovimientoInventario
    form_class = MovimientoManualForm
    template_name = 'logistica/movimiento_form.html'
    success_url = reverse_lazy('movimiento-list')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, "Movimiento de inventario registrado exitosamente.")
        return super().form_valid(form)

# ================================================================
# DESPACHO A PRODUCCIÓN (VISTA CORREGIDA)
# ================================================================
class DespachoProduccionView(LogisticaPermissionMixin, View):
    template_name = 'logistica/despacho_produccion.html'

    def get(self, request, *args, **kwargs):
        if Lote is None:
            messages.error(request, "La app 'produccion' no está instalada.")
            return redirect('dashboard-logistica')

        lotes_activos = Lote.objects.filter(activo=True)
        
        demanda_dict = {}
        for lote in lotes_activos:
            tipo_alimento = lote.tipo_alimento 
            demanda_kg = lote.alimento_diario_kg

            if demanda_kg > 0:
                if tipo_alimento in demanda_dict:
                    demanda_dict[tipo_alimento] += demanda_kg
                else:
                    demanda_dict[tipo_alimento] = demanda_kg
        
        data_despacho = []
        for tipo_alimento, demanda_kg in demanda_dict.items():
            
            insumo = Insumo.objects.filter(nombre=tipo_alimento).first()
            
            if insumo:
                stock_actual = insumo.stock_actual
                suficiente = stock_actual >= demanda_kg
                data_despacho.append({
                    'insumo_id': insumo.id,
                    'nombre': tipo_alimento, # Enviamos el nombre
                    'demanda_kg': demanda_kg,
                    'stock_actual': stock_actual,
                    'suficiente': suficiente
                })
            else:
                data_despacho.append({
                    'insumo_id': None,
                    'nombre': tipo_alimento, # Enviamos el nombre
                    'demanda_kg': demanda_kg,
                    'stock_actual': Decimal('0.00'),
                    'suficiente': False,
                })

        return render(request, self.template_name, {'data_despacho': data_despacho, 'total_items': len(data_despacho)})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        insumos_a_despachar_ids = request.POST.getlist('insumo_id')
        cantidades_a_despachar = request.POST.getlist('cantidad_kg')
        insumos_nombres = request.POST.getlist('insumo_nombre')
        
        items_para_despachar = []
        error_encontrado = False
        
        # --- 1. FASE DE VALIDACIÓN (SIN MODIFICAR LA BD) ---
        
        for i in range(len(insumos_a_despachar_ids)):
            insumo_id = insumos_a_despachar_ids[i]
            cantidad_str = cantidades_a_despachar[i]
            nombre_insumo = insumos_nombres[i]
            
            try:
                # ========================================================
                # AQUÍ ESTÁ LA CORRECCIÓN DE LA ESTUPIDEZ
                # Reemplazamos la coma (,) por un punto (.)
                # ========================================================
                cantidad_str_limpia = cantidad_str.replace(',', '.')
                cantidad = Decimal(cantidad_str_limpia)
                # ========================================================
                # FIN DE LA CORRECCIÓN
                # ========================================================

                if cantidad <= 0:
                    continue # No es un error, solo ignoramos
                
                # Error 1: Insumo no registrado en Logística
                if not insumo_id or insumo_id == 'None':
                    messages.error(request, f"Despacho fallido: El insumo '{nombre_insumo}' (demandado por Producción) no existe en tu inventario de Logística.")
                    error_encontrado = True
                    break 

                insumo = Insumo.objects.get(id=insumo_id)
                
                # Error 2: Stock insuficiente
                if insumo.stock_actual < cantidad:
                    messages.error(request, f"Stock insuficiente para '{insumo.nombre}'. Se necesitan {cantidad} kg, pero solo hay {insumo.stock_actual} kg.")
                    error_encontrado = True
                    raise transaction.TransactionManagementError("Stock insuficiente detectado")
                    
                items_para_despachar.append({
                    'insumo': insumo,
                    'cantidad': cantidad
                })
                
            except Insumo.DoesNotExist:
                 messages.error(request, f"Error: El insumo ID {insumo_id} ('{nombre_insumo}') no existe.")
                 error_encontrado = True
                 break
            except transaction.TransactionManagementError:
                # Captura el error de stock insuficiente y detiene el bucle
                error_encontrado = True
                break
            except Exception as e:
                # Aquí es donde fallaba antes, ahora mostrará el error de conversión
                messages.error(request, f"Error inesperado al validar '{nombre_insumo}'. (Error: {e})")
                error_encontrado = True
                break
        
        # --- 2. FASE DE EJECUCIÓN ---
        
        if error_encontrado:
            return redirect('despacho-produccion') # Los mensajes de error ya fueron agregados.
            
        if not items_para_despachar:
             messages.warning(request, "No se seleccionó ningún insumo para despachar.")
             return redirect('despacho-produccion')

        for item in items_para_despachar:
            MovimientoInventario.objects.create(
                insumo=item['insumo'],
                tipo_movimiento='SALIDA',
                cantidad=item['cantidad'],
                usuario=request.user,
                descripcion="Despacho diario automático a Producción"
            )
            
        messages.success(request, f"Despacho de {len(items_para_despachar)} insumo(s) completado. El stock ha sido actualizado.")
        return redirect('despacho-produccion')

# ================================================================
# VISTA DE PÁGINA DE REPORTES
# ================================================================
@login_required
def reporte_movimientos_view(request):
    """
    Esta vista solo muestra la página HTML con los filtros.
    El gráfico se carga por JavaScript.
    """
    # Preparar filtros de Mes/Año
    anios = range(datetime.now().year, 2023, -1) # Rango de años (desde 2024 hasta el actual)
    meses = [
        {"id": 1, "nombre": "Enero"}, {"id": 2, "nombre": "Febrero"},
        {"id": 3, "nombre": "Marzo"}, {"id": 4, "nombre": "Abril"},
        {"id": 5, "nombre": "Mayo"}, {"id": 6, "nombre": "Junio"},
        {"id": 7, "nombre": "Julio"}, {"id": 8, "nombre": "Agosto"},
        {"id": 9, "nombre": "Septiembre"}, {"id": 10, "nombre": "Octubre"},
        {"id": 11, "nombre": "Noviembre"}, {"id": 12, "nombre": "Diciembre"},
    ]
    
    context = {
        'anios': anios,
        'meses': meses,
        'current_anio': datetime.now().year,
        'current_mes': datetime.now().month
    }
    return render(request, 'logistica/reporte_movimientos.html', context)

# ================================================================
# VISTAS DE REPORTES (GRÁFICO Y TABLA)
# ================================================================

@login_required
def reporte_grafico_view(request):
    """
    Muestra la página del gráfico. Los datos se cargan por API.
    """
    # Preparar filtros de Mes/Año
    anios = range(datetime.now().year, 2023, -1)
    meses = [
        {"id": 1, "nombre": "Enero"}, {"id": 2, "nombre": "Febrero"},
        {"id": 3, "nombre": "Marzo"}, {"id": 4, "nombre": "Abril"},
        {"id": 5, "nombre": "Mayo"}, {"id": 6, "nombre": "Junio"},
        {"id": 7, "nombre": "Julio"}, {"id": 8, "nombre": "Agosto"},
        {"id": 9, "nombre": "Septiembre"}, {"id": 10, "nombre": "Octubre"},
        {"id": 11, "nombre": "Noviembre"}, {"id": 12, "nombre": "Diciembre"},
    ]
    
    context = {
        'anios': anios,
        'meses': meses,
        'current_anio': datetime.now().year,
        'current_mes': datetime.now().month
    }
    return render(request, 'logistica/reporte_grafico.html', context)


@login_required
def api_reporte_grafico(request):
    """
    API que alimenta el gráfico de líneas.
    """
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
    except ValueError:
        year = datetime.now().year
        month = datetime.now().month

    _, num_dias_mes = calendar.monthrange(year, month) 
    fecha_inicio_mes = datetime(year, month, 1).date()
    fecha_fin_mes = datetime(year, month, num_dias_mes).date()

    # Generar etiquetas para cada día del mes
    date_labels = [(fecha_inicio_mes + timedelta(days=i)).strftime('%d') for i in range(num_dias_mes)]
    
    # Consultar Entradas del mes
    entradas_db = MovimientoInventario.objects.filter(
        tipo_movimiento__in=['ENTRADA', 'AJUSTE_POS'],
        fecha__date__range=(fecha_inicio_mes, fecha_fin_mes)
    ).annotate(
        dia=TruncDay('fecha')
    ).values('dia').annotate(
        total=Sum('cantidad')
    ).order_by('dia')

    # Consultar Salidas del mes
    salidas_db = MovimientoInventario.objects.filter(
        tipo_movimiento__in=['SALIDA', 'AJUSTE_NEG'],
        fecha__date__range=(fecha_inicio_mes, fecha_fin_mes)
    ).annotate(
        dia=TruncDay('fecha')
    ).values('dia').annotate(
        total=Sum('cantidad')
    ).order_by('dia')

    # Mapear a diccionarios para acceso rápido (usando 'dd' como clave)
    entradas_map = {e['dia'].strftime('%d'): float(e['total']) for e in entradas_db}
    salidas_map = {s['dia'].strftime('%d'): float(s['total']) for s in salidas_db}
    
    # Llenar los datos para el gráfico
    entradas_data = [entradas_map.get(label, 0) for label in date_labels]
    salidas_data = [salidas_map.get(label, 0) for label in date_labels]

    data = {
        'chart_labels': date_labels,
        'chart_data_entradas': entradas_data,
        'chart_data_salidas': salidas_data,
    }
    return JsonResponse(data)

@login_required
def reporte_resumen_view(request):
    """
    Muestra la tabla de resumen de balance mensual y calcula saldos históricamente.
    """
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
    except ValueError:
        year = datetime.now().year
        month = datetime.now().month

    # Calcular fechas de inicio y fin del mes
    _, num_dias_mes = calendar.monthrange(year, month) 
    fecha_inicio_mes = datetime(year, month, 1).date()
    fecha_fin_mes = datetime(year, month, num_dias_mes).date()

    # Preparar filtros (misma lógica que antes)
    anios = range(datetime.now().year, 2023, -1)
    meses = [
        {"id": 1, "nombre": "Enero"}, {"id": 2, "nombre": "Febrero"},
        {"id": 3, "nombre": "Marzo"}, {"id": 4, "nombre": "Abril"},
        {"id": 5, "nombre": "Mayo"}, {"id": 6, "nombre": "Junio"},
        {"id": 7, "nombre": "Julio"}, {"id": 8, "nombre": "Agosto"},
        {"id": 9, "nombre": "Septiembre"}, {"id": 10, "nombre": "Octubre"},
        {"id": 11, "nombre": "Noviembre"}, {"id": 12, "nombre": "Diciembre"},
    ]

    # --- CONSULTA PRINCIPAL: Obtener movimientos consolidados del PERIODO ---
    insumos = Insumo.objects.all()
    resumen_data = []

    for insumo in insumos:
        # A. Movimientos dentro del período (Entradas y Salidas en el mes filtrado)
        
        entradas_mes = MovimientoInventario.objects.filter(
            insumo=insumo,
            tipo_movimiento__in=['ENTRADA', 'AJUSTE_POS'],
            fecha__date__range=(fecha_inicio_mes, fecha_fin_mes)
        ).aggregate(total=Coalesce(Sum('cantidad'), Decimal(0.0)))['total']

        salidas_mes = MovimientoInventario.objects.filter(
            insumo=insumo,
            tipo_movimiento__in=['SALIDA', 'AJUSTE_NEG'],
            fecha__date__range=(fecha_inicio_mes, fecha_fin_mes)
        ).aggregate(total=Coalesce(Sum('cantidad'), Decimal(0.0)))['total']
        
        # B. Movimientos ANTES del período (Para calcular el saldo inicial)
        
        # Necesitamos la suma de TODOS los movimientos de este insumo antes de la fecha_inicio_mes
        movimientos_anteriores = MovimientoInventario.objects.filter(
            insumo=insumo,
            fecha__date__lt=fecha_inicio_mes # Menor que el primer día del mes filtrado
        ).aggregate(
            entradas_ant=Coalesce(Sum('cantidad', filter=Q(tipo_movimiento__in=['ENTRADA', 'AJUSTE_POS'])), Decimal(0.0)),
            salidas_ant=Coalesce(Sum('cantidad', filter=Q(tipo_movimiento__in=['SALIDA', 'AJUSTE_NEG'])), Decimal(0.0))
        )
        
        # Saldo Inicial = Entradas Anteriores - Salidas Anteriores
        saldo_inicial = movimientos_anteriores['entradas_ant'] - movimientos_anteriores['salidas_ant']
        
        # Saldo Final del mes filtrado = Saldo Inicial + Entradas Mes - Salidas Mes
        saldo_final = saldo_inicial + entradas_mes - salidas_mes


        # REGLA DE VISIBILIDAD: Solo mostrar si hubo algún movimiento en el mes O si hay un saldo inicial
        if entradas_mes != 0 or salidas_mes != 0 or saldo_inicial != 0:
            resumen_data.append({
                'nombre': insumo.nombre,
                'unidad': insumo.get_unidad_medida_display(),
                'saldo_inicial': float(saldo_inicial),
                'total_entradas': float(entradas_mes),
                'total_salidas': float(salidas_mes),
                'saldo_final': float(saldo_final)
            })
            
    context = {
        'anios': anios,
        'meses': meses,
        'current_anio': year,
        'current_mes': month,
        'resumen_data': resumen_data,
        'mes_nombre': datetime(year, month, 1).strftime('%B %Y')
    }
    return render(request, 'logistica/reporte_resumen.html', context)



@login_required
def exportar_resumen_excel(request):
    """
    Genera un archivo Excel con el resumen de movimientos para el mes filtrado.
    """
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
    except ValueError:
        return HttpResponse("Filtros inválidos.", status=400)

    # Reusamos la lógica de cálculo (llamamos a la misma lógica de resumen)
    # NOTA: Debemos duplicar o modularizar la lógica de cálculo si no queremos
    # pasar todo el request. Aquí, por simplicidad, replicamos el cálculo.
    
    _, num_dias_mes = calendar.monthrange(year, month) 
    fecha_inicio_mes = datetime(year, month, 1).date()
    fecha_fin_mes = datetime(year, month, num_dias_mes).date()
    mes_nombre = datetime(year, month, 1).strftime('%B %Y')

    insumos = Insumo.objects.all()
    resumen_data = []

    for insumo in insumos:
        movimientos_anteriores = MovimientoInventario.objects.filter(
            insumo=insumo,
            fecha__date__lt=fecha_inicio_mes 
        ).aggregate(
            entradas_ant=Coalesce(Sum('cantidad', filter=Q(tipo_movimiento__in=['ENTRADA', 'AJUSTE_POS'])), Decimal(0.0)),
            salidas_ant=Coalesce(Sum('cantidad', filter=Q(tipo_movimiento__in=['SALIDA', 'AJUSTE_NEG'])), Decimal(0.0))
        )
        saldo_inicial = movimientos_anteriores['entradas_ant'] - movimientos_anteriores['salidas_ant']
        
        entradas_mes = MovimientoInventario.objects.filter(
            insumo=insumo,
            tipo_movimiento__in=['ENTRADA', 'AJUSTE_POS'],
            fecha__date__range=(fecha_inicio_mes, fecha_fin_mes)
        ).aggregate(total=Coalesce(Sum('cantidad'), Decimal(0.0)))['total']

        salidas_mes = MovimientoInventario.objects.filter(
            insumo=insumo,
            tipo_movimiento__in=['SALIDA', 'AJUSTE_NEG'],
            fecha__date__range=(fecha_inicio_mes, fecha_fin_mes)
        ).aggregate(total=Coalesce(Sum('cantidad'), Decimal(0.0)))['total']

        saldo_final = saldo_inicial + entradas_mes - salidas_mes

        if entradas_mes != 0 or salidas_mes != 0 or saldo_inicial != 0:
            resumen_data.append({
                'nombre': insumo.nombre,
                'unidad': insumo.get_unidad_medida_display(),
                'saldo_inicial': saldo_inicial,
                'total_entradas': entradas_mes,
                'total_salidas': salidas_mes,
                'saldo_final': saldo_final
            })

    # Generación del archivo Excel
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = f"Resumen {month}_{year}"

    # Encabezados
    headers = ["Insumo", "Unidad", "Saldo Inicial", "Total Entradas", "Total Salidas", "Saldo Final"]
    sheet.append(headers)

    # Datos
    for item in resumen_data:
        sheet.append([
            item['nombre'],
            item['unidad'],
            float(item['saldo_inicial']),
            float(item['total_entradas']),
            float(item['total_salidas']),
            float(item['saldo_final'])
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="Resumen_Logistica_{mes_nombre}.xlsx"'
    workbook.save(response)

    return response