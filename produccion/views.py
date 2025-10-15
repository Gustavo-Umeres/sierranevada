from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.db.models import F, Q, Sum, Value, FloatField, ExpressionWrapper, fields
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.utils import timezone
from django.db import transaction
from datetime import time, timedelta
from django.http import HttpResponse
import openpyxl
from django.db.models.functions import TruncDay
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

from .models import Bastidor, Artesa, Jaula, Lote, RegistroDiario, RegistroMortalidad, HistorialMovimiento,RegistroUnidad
from .forms import (
    BastidorForm, ArtesaForm, JaulaForm, LoteOvaCreateForm, 
    RegistroMortalidadForm, LoteTallaForm, LotePesoForm # <-- ELIMINADO DE AQUÍ
)
# ================================================================
# MIXIN DE PERMISOS Y VISTAS GENERALES
# ================================================================

class ProduccionPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='Produccion').exists()

@login_required
def welcome_view(request):
    return render(request, 'welcome.html')

@login_required
def dashboard_produccion(request):
    return render(request, 'produccion/dashboard.html')

# ================================================================
# VISTAS DE LISTA (LISTVIEWS)
# ================================================================

class BastidorListView(ProduccionPermissionMixin, ListView):
    model = Bastidor
    template_name = 'produccion/unidad_list.html'
    context_object_name = 'unidades'

    def get_queryset(self):
        return Bastidor.objects.select_related('lote_actual').order_by('codigo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'titulo_etapa': 'Gestión de Bastidores (Ovas)',
            'tipo_unidad_slug': 'bastidor',
            'tipo_unidad_singular': 'Bastidor',
            'tipo_unidad_plural': 'Bastidores',
            'add_url': reverse_lazy('bastidor-create'),
            'update_url_name': 'bastidor-update',
            'delete_url_name': 'bastidor-delete',
            'es_etapa_final': False,
        })
        return context

class ArtesaListView(ProduccionPermissionMixin, ListView):
    model = Artesa
    template_name = 'produccion/unidad_list.html'
    context_object_name = 'unidades'

    def get_queryset(self):
        return Artesa.objects.prefetch_related('lotes').order_by('codigo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'titulo_etapa': 'Gestión de Artesas (Alevines)',
            'tipo_unidad_slug': 'artesa',
            'tipo_unidad_singular': 'Artesa',
            'tipo_unidad_plural': 'Artesas',
            'add_url': reverse_lazy('artesa-create'),
            'update_url_name': 'artesa-update',
            'delete_url_name': 'artesa-delete',
            'es_etapa_final': False,
        })
        return context

class JuvenilListView(ProduccionPermissionMixin, ListView):
    model = Jaula
    template_name = 'produccion/unidad_list.html'
    context_object_name = 'unidades'

    def get_queryset(self):
        return Jaula.objects.filter(tipo='JUVENIL').prefetch_related('lotes').order_by('codigo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'titulo_etapa': 'Gestión de Juveniles',
            'tipo_unidad_slug': 'jaula',
            'tipo_unidad_singular': 'Jaula',
            'tipo_unidad_plural': 'Jaulas',
            'add_url': reverse_lazy('jaula-create'),
            'update_url_name': 'jaula-update',
            'delete_url_name': 'jaula-delete',
            'es_etapa_final': False,
            'jaula_tipo': 'JUVENIL',
        })
        return context
    
class EngordeListView(ProduccionPermissionMixin, ListView):
    model = Jaula
    template_name = 'produccion/unidad_list.html'
    context_object_name = 'unidades'

    def get_queryset(self):
        return Jaula.objects.filter(tipo='ENGORDE').prefetch_related('lotes').order_by('codigo')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'titulo_etapa': 'Gestión de Engorde',
            'tipo_unidad_slug': 'jaula',
            'tipo_unidad_singular': 'Jaula',
            'tipo_unidad_plural': 'Jaulas',
            'add_url': reverse_lazy('jaula-create'),
            'update_url_name': 'jaula-update',
            'delete_url_name': 'jaula-delete',
            'es_etapa_final': True,
            'jaula_tipo': 'ENGORDE',
        })
        return context

# ================================================================
# VISTAS DE CREACIÓN / EDICIÓN / BORRADO (CUD)
# ================================================================

class BastidorCreateView(ProduccionPermissionMixin, CreateView):
    model = Bastidor
    form_class = BastidorForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('bastidor-list')
    extra_context = {'tipo_unidad': 'Bastidor'}

    def form_valid(self, form):
        cantidad = form.cleaned_data.get('cantidad_a_crear', 1)
        capacidad = form.cleaned_data['capacidad_maxima_unidades']
        with transaction.atomic():
            for i in range(cantidad):
                Bastidor.objects.create(capacidad_maxima_unidades=capacidad)
        messages.success(self.request, f"{cantidad} bastidor(es) han sido creados con éxito.")
        return redirect(self.success_url)

class BastidorUpdateView(ProduccionPermissionMixin, UpdateView):
    model = Bastidor
    form_class = BastidorForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('bastidor-list')
    extra_context = {'tipo_unidad': 'Bastidor'}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields.pop('cantidad_a_crear', None)
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"El bastidor con código '{self.object.codigo}' ha sido actualizado.")
        return response

class BastidorDeleteView(ProduccionPermissionMixin, DeleteView):
    model = Bastidor
    template_name = 'produccion/unidad_confirm_delete.html' 
    success_url = reverse_lazy('bastidor-list')
    def form_valid(self, form):
        messages.success(self.request, f"El bastidor '{self.object.codigo}' ha sido eliminado.")
        return super().form_valid(form)


class ArtesaCreateView(ProduccionPermissionMixin, CreateView):
    model = Artesa
    form_class = ArtesaForm
    template_name = 'produccion/unidad_biomasa_form.html'
    success_url = reverse_lazy('artesa-list')
    extra_context = {'tipo_unidad': 'Artesa'}

    def form_valid(self, form):
        cantidad = form.cleaned_data.get('cantidad_a_crear', 1)
        with transaction.atomic():
            for i in range(cantidad):
                Artesa.objects.create(
                    forma=form.cleaned_data['forma'],
                    largo_m=form.cleaned_data.get('largo_m'),
                    ancho_m=form.cleaned_data.get('ancho_m'),
                    diametro_m=form.cleaned_data.get('diametro_m'),
                    alto_m=form.cleaned_data.get('alto_m'),
                    densidad_siembra_kg_m3=form.cleaned_data['densidad_siembra_kg_m3'],
                )
        messages.success(self.request, f"{cantidad} artesa(s) han sido creadas con éxito.")
        return redirect(self.success_url)


class ArtesaUpdateView(ProduccionPermissionMixin, UpdateView):
    model = Artesa
    form_class = ArtesaForm
    template_name = 'produccion/unidad_biomasa_form.html' 
    success_url = reverse_lazy('artesa-list')
    extra_context = {'tipo_unidad': 'Artesa'}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields.pop('cantidad_a_crear', None)
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"La artesa con código '{self.object.codigo}' ha sido actualizada.")
        return response

class ArtesaDeleteView(ProduccionPermissionMixin, DeleteView):
    model = Artesa
    template_name = 'produccion/unidad_confirm_delete.html'
    success_url = reverse_lazy('artesa-list')
    
    def form_valid(self, form):
        messages.success(self.request, f"La artesa '{self.object.codigo}' ha sido eliminada.")
        return super().form_valid(form)

class JaulaCreateView(ProduccionPermissionMixin, CreateView):
    model = Jaula
    form_class = JaulaForm
    template_name = 'produccion/unidad_biomasa_form.html'

    def get_initial(self):
        initial = super().get_initial()
        tipo_jaula_url = self.request.GET.get('tipo')
        if tipo_jaula_url in ['JUVENIL', 'ENGORDE']:
            initial['tipo'] = tipo_jaula_url
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo_jaula_url = self.request.GET.get('tipo')
        if tipo_jaula_url == 'JUVENIL':
            context['tipo_unidad'] = 'Jaula Juvenil'
        elif tipo_jaula_url == 'ENGORDE':
            context['tipo_unidad'] = 'Jaula de Engorde'
        else:
            context['tipo_unidad'] = 'Jaula'
        return context

    def form_valid(self, form):
        cantidad = form.cleaned_data.get('cantidad_a_crear', 1)
        with transaction.atomic():
            for i in range(cantidad):
                Jaula.objects.create(
                    tipo=form.cleaned_data['tipo'],
                    forma=form.cleaned_data['forma'],
                    largo_m=form.cleaned_data.get('largo_m'),
                    ancho_m=form.cleaned_data.get('ancho_m'),
                    diametro_m=form.cleaned_data.get('diametro_m'),
                    alto_m=form.cleaned_data.get('alto_m'),
                    densidad_siembra_kg_m3=form.cleaned_data['densidad_siembra_kg_m3'],
                )
        messages.success(self.request, f"{cantidad} jaula(s) han sido creadas con éxito.")
        
        if form.cleaned_data['tipo'] == 'JUVENIL':
            return redirect('juvenil-list')
        return redirect('engorde-list') # <-- CORREGIDO
    
class JaulaUpdateView(ProduccionPermissionMixin, UpdateView):
    model = Jaula
    form_class = JaulaForm
    template_name = 'produccion/unidad_biomasa_form.html'

    def get_success_url(self):
        """Redirige a la lista correcta (Juvenil o Engorde) después de guardar."""
        if self.object.tipo == 'JUVENIL':
            return reverse_lazy('juvenil-list')
        return reverse_lazy('engorde-list')

    def get_form(self, form_class=None):
        """Elimina el campo 'cantidad_a_crear' del formulario de edición."""
        form = super().get_form(form_class)
        form.fields.pop('cantidad_a_crear', None)
        return form

    def get_context_data(self, **kwargs):
        """Añade un título específico ('Jaula Juvenil' o 'Jaula de Engorde') a la plantilla."""
        context = super().get_context_data(**kwargs)
        if self.object.tipo == 'JUVENIL':
            context['tipo_unidad'] = 'Jaula Juvenil'
        elif self.object.tipo == 'ENGORDE':
            context['tipo_unidad'] = 'Jaula de Engorde'
        return context

    def form_valid(self, form):
        """Muestra un mensaje de éxito después de actualizar."""
        response = super().form_valid(form)
        messages.success(self.request, f"La jaula con código '{self.object.codigo}' ha sido actualizada.")
        return response

class JaulaDeleteView(ProduccionPermissionMixin, DeleteView):
    model = Jaula
    template_name = 'produccion/unidad_confirm_delete.html'
    success_url = reverse_lazy('dashboard-produccion')
    
    def form_valid(self, form):
        messages.success(self.request, f"La jaula '{self.object.codigo}' ha sido eliminada.")
        return super().form_valid(form)

# ================================================================
# VISTAS DE API (JSON)
# ================================================================

@login_required
def unidad_detail_json(request, pk, tipo_unidad):
    data = {}
    unidad_model_map = {'bastidor': Bastidor, 'artesa': Artesa, 'jaula': Jaula}
    UnidadModel = unidad_model_map.get(tipo_unidad)
    if not UnidadModel: 
        return JsonResponse({'error': 'Tipo de unidad no válido'}, status=400)
    
    if tipo_unidad == 'bastidor':
        unidad = get_object_or_404(UnidadModel.objects.select_related('lote_actual'), pk=pk)
    else:
        unidad = get_object_or_404(UnidadModel.objects.prefetch_related('lotes'), pk=pk)
    
    hoy = timezone.now().date()
    registros_diarios_hoy = {}
    if tipo_unidad != 'bastidor':
        lotes_qs = unidad.lotes.all()
        if lotes_qs.exists():
            registros = RegistroDiario.objects.filter(lote__in=lotes_qs, fecha=hoy)
            for registro in registros:
                registros_diarios_hoy[registro.lote_id] = {
                    'alimentacion_hoy': registro.alimentacion_realizada,
                    'limpieza_hoy': registro.limpieza_realizada
                }
    
    lotes_info = []
    if tipo_unidad == 'bastidor':
        lote = getattr(unidad, 'lote_actual', None)
        if lote:
            registro_lote = RegistroDiario.objects.filter(lote=lote, fecha=hoy).first()
            lotes_info.append({
                'id': lote.id, 'codigo': lote.codigo_lote,
                'cantidad_peces': lote.cantidad_total_peces,
                'dias_en_etapa': (hoy - lote.fecha_ingreso_etapa).days if lote.fecha_ingreso_etapa else 0,
                'limpieza_hoy': registro_lote.limpieza_realizada if registro_lote else False,
            })
    else: 
        for lote in unidad.lotes.all():
            registro_lote = registros_diarios_hoy.get(lote.id, {})
            lotes_info.append({
                'id': lote.id, 'codigo': lote.codigo_lote,
                'cantidad_peces': lote.cantidad_total_peces,
                'biomasa_lote_kg': float(lote.biomasa_kg),
                'dias_en_etapa': (hoy - lote.fecha_ingreso_etapa).days if lote.fecha_ingreso_etapa else 0,
                'talla_min_cm': float(lote.talla_min_cm) if lote.talla_min_cm is not None else None,
                'talla_max_cm': float(lote.talla_max_cm) if lote.talla_max_cm is not None else None,
                'peso_promedio_pez_gr': float(lote.peso_promedio_pez_gr) if lote.peso_promedio_pez_gr is not None else None,
                'racion_alimentaria_porcentaje': float(lote.racion_alimentaria_porcentaje),
                'alimento_diario_kg': float(lote.alimento_diario_kg),
                'tipo_alimento': lote.tipo_alimento,
                'alimentacion_hoy': registro_lote.get('alimentacion_hoy', False),
                'limpieza_hoy': registro_lote.get('limpieza_hoy', False),
            })

    data['unidad'] = {
        'id': unidad.id, 'codigo': str(unidad),
        'capacidad_maxima_kg': float(getattr(unidad, 'capacidad_maxima_kg', 0)),
        'capacidad_maxima_unidades': getattr(unidad, 'capacidad_maxima_unidades', None),
        'biomasa_actual': float(getattr(unidad, 'biomasa_actual', 0)),
        'biomasa_disponible': float(getattr(unidad, 'biomasa_disponible', 0)),
        'alimento_diario_total_kg': float(getattr(unidad, 'alimento_diario_total_kg', 0)),
    }
    data['lotes'] = lotes_info
    return JsonResponse(data)


@login_required
def lote_ova_create_view(request, bastidor_id):
    bastidor = get_object_or_404(Bastidor, pk=bastidor_id)
    if request.method == 'POST':
        form = LoteOvaCreateForm(request.POST)
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad_total_peces']
            if cantidad <= 0: return JsonResponse({'error': 'La cantidad debe ser mayor que cero.'}, status=400)
            if cantidad > bastidor.capacidad_maxima_unidades: return JsonResponse({'error': f"La cantidad supera la capacidad máxima ({bastidor.capacidad_maxima_unidades})."}, status=400)
            if not bastidor.esta_disponible: return JsonResponse({'error': 'Este bastidor ya está ocupado.'}, status=400)
            
            lote = form.save(commit=False)
            lote.etapa_actual = 'OVAS'
            lote.bastidor = bastidor
            lote.save()
            
            bastidor.esta_disponible = False
            bastidor.save()
            return JsonResponse({'success': True, 'message': 'Lote de ovas creado con éxito.'})
        else:
            return JsonResponse({'error': 'Datos inválidos.', 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def registrar_mortalidad_json(request, lote_id):
    lote = get_object_or_404(Lote, pk=lote_id)
    if request.method == 'POST':
        form = RegistroMortalidadForm(request.POST)
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad']
            if cantidad > 0 and cantidad <= lote.cantidad_total_peces:
                RegistroMortalidad.objects.create(lote=lote, cantidad=cantidad, registrado_por=request.user)
                HistorialMovimiento.objects.create(
                lote=lote,
                tipo_movimiento='BAJAS',
                descripcion=f"Se registraron {cantidad} bajas. Registrado por: {request.user.username}",
                cantidad_afectada=cantidad
                )
                lote.cantidad_total_peces = F('cantidad_total_peces') - cantidad
                lote.save()
                lote.refresh_from_db()
                return JsonResponse({
                    'success': True, 
                    'nueva_cantidad': lote.cantidad_total_peces,
                    'nuevo_alimento': float(lote.alimento_diario_kg) 
                })
            else:
                return JsonResponse({'error': 'La cantidad es inválida.'}, status=400)
        else:
            return JsonResponse({'error': 'Dato inválido.', 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def marcar_tarea_json(request, lote_id, tarea):
    lote = get_object_or_404(Lote, pk=lote_id)
    if request.method == 'POST':
        registro, _ = lote.registros_diarios.get_or_create(fecha=timezone.now().date())
        if tarea == 'alimentacion':
            registro.alimentacion_realizada = True
        elif tarea == 'limpieza':
            registro.limpieza_realizada = True
        registro.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def listar_artesas_disponibles_json(request, lote_id_origen):
    lote_origen = get_object_or_404(Lote, pk=lote_id_origen)
    biomasa_a_mover = 0
    if lote_origen.etapa_actual == 'OVAS':
        PESO_ESTANDAR_ALEVIN_GR = 0.20
        biomasa_a_mover = (lote_origen.cantidad_total_peces * PESO_ESTANDAR_ALEVIN_GR) / 1000
    else:
        biomasa_a_mover = float(lote_origen.biomasa_kg)
    artesas = Artesa.objects.annotate(
        biomasa_actual_kg=Coalesce(Sum(F('lotes__cantidad_total_peces') * F('lotes__peso_promedio_pez_gr') / 1000.0), Value(0.0), output_field=FloatField())
    ).annotate(
        biomasa_disponible_kg=ExpressionWrapper(F('capacidad_maxima_kg') - F('biomasa_actual_kg'), output_field=FloatField())
    ).filter(biomasa_disponible_kg__gte=biomasa_a_mover)
    if lote_origen.artesa:
        artesas = artesas.exclude(pk=lote_origen.artesa.pk)
    data = [{'id': artesa.id, 'codigo': str(artesa), 'capacidad_maxima_kg': float(artesa.capacidad_maxima_kg), 'biomasa_actual_kg': round(artesa.biomasa_actual_kg, 2), 'biomasa_disponible_kg': round(artesa.biomasa_disponible_kg, 2)} for artesa in artesas]
    return JsonResponse({'artesas': data, 'biomasa_a_mover': round(biomasa_a_mover, 2)}, safe=False)


@login_required
def mover_lote_a_artesa(request, lote_id, artesa_id):
    if request.method == 'POST':
        lote = get_object_or_404(Lote, pk=lote_id)
        nueva_artesa = get_object_or_404(Artesa, pk=artesa_id)
        antiguo_bastidor = lote.bastidor
        PESO_ESTANDAR_ALEVIN_GR = 0.20
        lote_biomasa = (lote.cantidad_total_peces * PESO_ESTANDAR_ALEVIN_GR) / 1000
        if lote_biomasa > nueva_artesa.biomasa_disponible:
            error_msg = f"La biomasa del lote ({lote_biomasa:.2f} kg) supera la capacidad disponible ({nueva_artesa.biomasa_disponible:.2f} kg)."
            return JsonResponse({'error': error_msg}, status=400)
        lote.bastidor = None
        lote.artesa = nueva_artesa
        lote.etapa_actual = 'ALEVINES'
        lote.fecha_ingreso_etapa = timezone.now().date()
        lote.peso_promedio_pez_gr = PESO_ESTANDAR_ALEVIN_GR
        lote.talla_min_cm = 2.61
        lote.talla_max_cm = 2.61
        lote.save()
        if antiguo_bastidor:
            antiguo_bastidor.esta_disponible = True
            antiguo_bastidor.save()
        return JsonResponse({'success': True, 'message': 'El lote ha sido movido a la artesa con éxito.'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def lote_definir_talla_json(request, pk):
    lote = get_object_or_404(Lote, pk=pk)
    if request.method == 'POST':
        form = LoteTallaForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Datos inválidos', 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def lote_definir_peso_json(request, pk):
    lote = get_object_or_404(Lote, pk=pk)
    if request.method == 'POST':
        form = LotePesoForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            lote.refresh_from_db()
            return JsonResponse({'success': True, 'nuevo_alimento': float(lote.alimento_diario_kg)})
        else:
            return JsonResponse({'error': 'Datos inválidos', 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def listar_jaulas_disponibles_json(request, lote_id):
    lote = get_object_or_404(Lote, pk=lote_id)
    lote_biomasa = float(lote.biomasa_kg)
    jaulas_qs = Jaula.objects.annotate(
        biomasa_actual_kg=Coalesce(Sum(F('lotes__cantidad_total_peces') * F('lotes__peso_promedio_pez_gr') / 1000.0), Value(0.0), output_field=FloatField())
    ).annotate(
        biomasa_disponible_kg=ExpressionWrapper(F('capacidad_maxima_kg') - F('biomasa_actual_kg'), output_field=FloatField())
    ).filter(
        tipo='JUVENIL',
        biomasa_disponible_kg__gte=lote_biomasa
    )
    data = [{'id': jaula.id, 'codigo': str(jaula), 'capacidad_maxima_kg': float(jaula.capacidad_maxima_kg), 'biomasa_actual_kg': round(jaula.biomasa_actual_kg, 2), 'biomasa_disponible_kg': round(jaula.biomasa_disponible_kg, 2)} for jaula in jaulas_qs]
    return JsonResponse({'jaulas': data, 'biomasa_a_mover': round(lote_biomasa, 2)}, safe=False)


@login_required
def listar_jaulas_disponibles_engorde_json(request, lote_id):
    lote = get_object_or_404(Lote, pk=lote_id)
    lote_biomasa = float(lote.biomasa_kg)

    jaulas_qs = Jaula.objects.annotate(
        biomasa_actual_kg=Coalesce(Sum(F('lotes__cantidad_total_peces') * F('lotes__peso_promedio_pez_gr') / 1000.0), Value(0.0), output_field=FloatField())
    ).annotate(
        biomasa_disponible_kg=ExpressionWrapper(F('capacidad_maxima_kg') - F('biomasa_actual_kg'), output_field=FloatField())
    ).filter(
        tipo='ENGORDE',
        biomasa_disponible_kg__gte=lote_biomasa
    )
    
    # --- CORRECCIÓN CLAVE ---
    # Se itera sobre los objetos para convertir Decimal a float manualmente
    data = [{
        'id': jaula.id, 
        'codigo': str(jaula),
        'capacidad_maxima_kg': float(jaula.capacidad_maxima_kg),
        'biomasa_actual_kg': round(jaula.biomasa_actual_kg, 2),
        'biomasa_disponible_kg': round(jaula.biomasa_disponible_kg, 2)
    } for jaula in jaulas_qs]
    
    return JsonResponse({'jaulas': data, 'biomasa_a_mover': round(lote_biomasa, 2)}, safe=False)

@login_required
@transaction.atomic
def mover_lote_a_jaula(request, lote_id):
    if request.method == 'POST':
        lote_origen = get_object_or_404(Lote, pk=lote_id)
        jaula_destino_id = request.POST.get('jaula_destino') 
        jaula_destino = get_object_or_404(Jaula, pk=jaula_destino_id)
        
        cantidad_str = request.POST.get('cantidad')
        if not cantidad_str:
            cantidad = lote_origen.cantidad_total_peces
        else:
            try:
                cantidad = int(cantidad_str)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'La cantidad debe ser un número válido.'}, status=400)
        
        if cantidad <= 0 or cantidad > lote_origen.cantidad_total_peces: 
            return JsonResponse({'error': 'La cantidad a mover es inválida.'}, status=400)

        biomasa_a_mover = (lote_origen.biomasa_kg / lote_origen.cantidad_total_peces) * cantidad if lote_origen.cantidad_total_peces > 0 else 0
        
        if float(biomasa_a_mover) > float(jaula_destino.biomasa_disponible):
            error_msg = f"La biomasa a mover ({biomasa_a_mover:.2f} kg) supera la capacidad disponible de la jaula ({jaula_destino.biomasa_disponible:.2f} kg)."
            return JsonResponse({'error': error_msg}, status=400)

        if cantidad == lote_origen.cantidad_total_peces:
            lote_origen.artesa = None
            lote_origen.jaula = jaula_destino
            lote_origen.etapa_actual = 'JUVENILES'
            lote_origen.fecha_ingreso_etapa = timezone.now().date()
            lote_origen.save()
            message = 'El lote completo ha sido movido a la jaula con éxito.'
        else:
            nuevo_lote = Lote.objects.create(
                etapa_actual='JUVENILES',
                cantidad_total_peces=cantidad,
                jaula=jaula_destino,
                talla_min_cm=lote_origen.talla_min_cm,
                talla_max_cm=lote_origen.talla_max_cm,
                peso_promedio_pez_gr=lote_origen.peso_promedio_pez_gr,
            )
            lote_origen.cantidad_total_peces = F('cantidad_total_peces') - cantidad
            lote_origen.save()
            lote_origen.refresh_from_db()
            message = f'{cantidad} peces movidos al nuevo lote {nuevo_lote.codigo_lote}.'

        return JsonResponse({'success': True, 'message': message})
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
@transaction.atomic
def reasignar_alevines_json(request, lote_origen_id):
    if request.method == 'POST':
        lote_origen = get_object_or_404(Lote, pk=lote_origen_id)
        artesa_destino_id = request.POST.get('artesa_destino') 
        artesa_destino = get_object_or_404(Artesa, pk=artesa_destino_id)

        cantidad_str = request.POST.get('cantidad')
        if not cantidad_str:
            return JsonResponse({'error': 'Debes especificar una cantidad para reasignar.'}, status=400)
        try:
            cantidad = int(cantidad_str)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'La cantidad debe ser un número válido.'}, status=400)

        if cantidad <= 0 or cantidad >= lote_origen.cantidad_total_peces:
            return JsonResponse({'error': 'La cantidad a mover es inválida (no puedes reasignar el lote completo).'}, status=400)
            
        biomasa_a_mover = (lote_origen.biomasa_kg / lote_origen.cantidad_total_peces) * cantidad if lote_origen.cantidad_total_peces > 0 and lote_origen.peso_promedio_pez_gr else 0
        
        if biomasa_a_mover > artesa_destino.biomasa_disponible:
            error_msg = f"La biomasa a mover ({biomasa_a_mover:.2f} kg) supera la capacidad disponible de la artesa ({artesa_destino.biomasa_disponible:.2f} kg)."
            return JsonResponse({'error': error_msg}, status=400)
        
        nuevo_lote = Lote.objects.create(etapa_actual='ALEVINES', cantidad_total_peces=cantidad, artesa=artesa_destino, peso_promedio_pez_gr=lote_origen.peso_promedio_pez_gr)
        lote_origen.cantidad_total_peces = F('cantidad_total_peces') - cantidad
        lote_origen.save()
        lote_origen.refresh_from_db()
        
        return JsonResponse({'success': True, 'message': f'{cantidad} alevines reasignados al lote {nuevo_lote.codigo_lote}.'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def listar_otras_jaulas_disponibles_json(request, lote_id_origen):
    lote_origen = get_object_or_404(Lote, pk=lote_id_origen)
    lote_biomasa = float(lote_origen.biomasa_kg)
    
    queryset = Jaula.objects.annotate(
        biomasa_actual_kg=Coalesce(Sum(F('lotes__cantidad_total_peces') * F('lotes__peso_promedio_pez_gr') / 1000.0), Value(0.0), output_field=FloatField())
    ).annotate(
        biomasa_disponible_kg=ExpressionWrapper(F('capacidad_maxima_kg') - F('biomasa_actual_kg'), output_field=FloatField())
    )

    if lote_origen.jaula:
        queryset = queryset.exclude(pk=lote_origen.jaula.pk)
        
    jaulas = [{'id': jaula.id, 'codigo': str(jaula), 'capacidad_maxima_kg': float(jaula.capacidad_maxima_kg), 'biomasa_actual_kg': round(jaula.biomasa_actual_kg, 2), 'biomasa_disponible_kg': round(jaula.biomasa_disponible_kg, 2)} for jaula in queryset]
    
    return JsonResponse({'jaulas': jaulas, 'biomasa_a_mover': round(lote_biomasa, 2)}, safe=False)


@login_required
@transaction.atomic
def reasignar_engorde_json(request, lote_origen_id):
    if request.method == 'POST':
        lote_origen = get_object_or_404(Lote, pk=lote_origen_id)
        jaula_destino_id = request.POST.get('jaula_destino')
        jaula_destino = get_object_or_404(Jaula, pk=jaula_destino_id)
        
        cantidad_str = request.POST.get('cantidad')
        if not cantidad_str:
            return JsonResponse({'error': 'Debes especificar una cantidad para reasignar.'}, status=400)
        try:
            cantidad = int(cantidad_str)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'La cantidad debe ser un número válido.'}, status=400)

        if cantidad <= 0 or cantidad >= lote_origen.cantidad_total_peces:
            return JsonResponse({'error': 'La cantidad a mover es inválida (no puedes reasignar el lote completo).'}, status=400)

        biomasa_a_mover = (lote_origen.biomasa_kg / lote_origen.cantidad_total_peces) * cantidad if lote_origen.cantidad_total_peces > 0 and lote_origen.peso_promedio_pez_gr else 0

        if biomasa_a_mover > jaula_destino.biomasa_disponible:
            error_msg = f"La biomasa a mover ({biomasa_a_mover:.2f} kg) supera la capacidad disponible de la jaula ({jaula_destino.biomasa_disponible:.2f} kg)."
            return JsonResponse({'error': error_msg}, status=400)
        
        nuevo_lote = Lote.objects.create(etapa_actual='ENGORDE', cantidad_total_peces=cantidad, jaula=jaula_destino, talla_min_cm=lote_origen.talla_min_cm, talla_max_cm=lote_origen.talla_max_cm, peso_promedio_pez_gr=lote_origen.peso_promedio_pez_gr)
        lote_origen.cantidad_total_peces = F('cantidad_total_peces') - cantidad
        lote_origen.save()
        lote_origen.refresh_from_db()
        
        return JsonResponse({'success': True, 'message': f'{cantidad} peces reasignados al lote {nuevo_lote.codigo_lote}.'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def get_notifications_json(request):
    notifications = []
    now = timezone.now()
    
    if request.user.groups.filter(name='Produccion').exists() or request.user.is_staff:
        
        lotes_ovas_vencidos = Lote.objects.filter(
            etapa_actual='OVAS',
            fecha_ingreso_etapa__lte=now.date() - timedelta(days=15)
        )
        for lote in lotes_ovas_vencidos:
            notifications.append({
                'area': 'Producción',
                'message': f"El lote {lote.codigo_lote} en {lote.bastidor} debe ser movido a artesa.",
                'url': reverse_lazy('bastidor-list')
            })

        alevines_para_juvenil = Lote.objects.filter(
            etapa_actual='ALEVINES',
            talla_max_cm__gte=8
        )
        for lote in alevines_para_juvenil:
            notifications.append({
                'area': 'Producción',
                'message': f"El lote {lote.codigo_lote} en {lote.artesa} está listo para mover a jaula de juveniles.",
                'url': reverse_lazy('artesa-list')
            })

        juveniles_para_engorde = Lote.objects.filter(
            etapa_actual='JUVENILES',
            talla_max_cm__gte=15
        )
        for lote in juveniles_para_engorde:
            notifications.append({
                'area': 'Producción',
                'message': f"El lote {lote.codigo_lote} en {lote.jaula} está listo para mover a jaula de engorde.",
                'url': reverse_lazy('juvenil-list')
            })

    if request.user.groups.filter(name__in=['Comercializacion', 'Produccion']).exists() or request.user.is_staff:
        lotes_para_venta = Lote.objects.filter(
            etapa_actual='ENGORDE',
            talla_max_cm__gte=25
        )
        for lote in lotes_para_venta:
            notifications.append({
                'area': 'Comercialización',
                'message': f"El lote {lote.codigo_lote} en {lote.jaula} está listo para la venta.",
                'url': reverse_lazy('engorde-list')
            })

    return JsonResponse(notifications, safe=False)


@login_required
@transaction.atomic
def mover_lote_a_jaula_engorde(request, lote_id):
    """
    Mueve un lote (completo o parcial) de una jaula de JUVENILES a una de ENGORDE.
    """
    if request.method == 'POST':
        lote_origen = get_object_or_404(Lote, pk=lote_id)
        jaula_destino_id = request.POST.get('jaula_destino')
        jaula_destino = get_object_or_404(Jaula, pk=jaula_destino_id)
        
        cantidad_str = request.POST.get('cantidad')
        if not cantidad_str:
            cantidad = lote_origen.cantidad_total_peces
        else:
            try:
                cantidad = int(cantidad_str)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'La cantidad debe ser un número válido.'}, status=400)

        if cantidad <= 0 or cantidad > lote_origen.cantidad_total_peces: 
            return JsonResponse({'error': 'La cantidad a mover es inválida.'}, status=400)

        biomasa_a_mover = (lote_origen.biomasa_kg / lote_origen.cantidad_total_peces) * cantidad if lote_origen.cantidad_total_peces > 0 else 0
        
        if float(biomasa_a_mover) > float(jaula_destino.biomasa_disponible):
            error_msg = f"La biomasa a mover ({biomasa_a_mover:.2f} kg) supera la capacidad disponible ({jaula_destino.biomasa_disponible:.2f} kg)."
            return JsonResponse({'error': error_msg}, status=400)

        if cantidad == lote_origen.cantidad_total_peces:
            lote_origen.jaula = jaula_destino
            lote_origen.etapa_actual = 'ENGORDE'
            lote_origen.fecha_ingreso_etapa = timezone.now().date()
            lote_origen.save()
            message = 'El lote completo ha sido movido a la jaula de engorde.'
        else:
            # Lógica para dividir el lote
            nuevo_lote = Lote.objects.create(
                etapa_actual='ENGORDE',
                cantidad_total_peces=cantidad,
                jaula=jaula_destino,
                talla_min_cm=lote_origen.talla_min_cm,
                talla_max_cm=lote_origen.talla_max_cm,
                peso_promedio_pez_gr=lote_origen.peso_promedio_pez_gr,
            )
            lote_origen.cantidad_total_peces = F('cantidad_total_peces') - cantidad
            lote_origen.save()
            message = f'{cantidad} peces movidos al nuevo lote {nuevo_lote.codigo_lote} en etapa de engorde.'

        return JsonResponse({'success': True, 'message': message})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

class HistorialTrazabilidadView(ProduccionPermissionMixin, ListView):
    model = Lote
    template_name = 'produccion/historial_trazabilidad.html'
    context_object_name = 'lotes_data' # Cambiamos el nombre para más claridad
    paginate_by = 30

    def get_queryset(self):
        # La consulta base solo filtra los lotes
        queryset = Lote.objects.filter(
            etapa_actual__in=['ALEVINES', 'JUVENILES', 'ENGORDE']
        ).prefetch_related('registros_mortalidad').order_by('-fecha_ingreso_etapa')
        
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')

        if year:
            queryset = queryset.filter(fecha_ingreso_etapa__year=year)
        if month:
            queryset = queryset.filter(fecha_ingreso_etapa__month=month)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- LÓGICA DE CÁLCULO MEJORADA ---
        # Preparamos una lista con todos los datos ya calculados en Python
        lotes_procesados = []
        for lote in context['lotes_data']:
            peces_muertos = lote.registros_mortalidad.aggregate(total=Coalesce(Sum('cantidad'), 0))['total']
            cantidad_inicial = lote.cantidad_total_peces + peces_muertos
            porc_mort = (peces_muertos / cantidad_inicial) * 100 if cantidad_inicial > 0 else 0
            
            lotes_procesados.append({
                'lote': lote,
                'peces_muertos': peces_muertos,
                'porc_mort': round(porc_mort, 2)
            })
        
        context['lotes_data'] = lotes_procesados # Reemplazamos la lista original por la procesada
        
        # Filtros
        context['years'] = range(timezone.now().year, 2022, -1)
        context['months'] = [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ]
        context['selected_year'] = self.request.GET.get('year', '')
        context['selected_month'] = self.request.GET.get('month', '')
        return context



@login_required
def exportar_historial_excel(request):
    queryset = HistorialMovimiento.objects.select_related('lote')
    year = request.GET.get('year')
    month = request.GET.get('month')
    if year:
        queryset = queryset.filter(fecha__year=year)
    if month:
        queryset = queryset.filter(fecha__month=month)

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Historial de Trazabilidad"

    headers = ["Fecha", "Lote", "Tipo de Movimiento", "Descripción", "Cantidad Afectada"]
    sheet.append(headers)

    for item in queryset:
        # --- LÍNEA CORREGIDA ---
        # Hacemos que la fecha sea "naive" (sin zona horaria) antes de guardarla
        fecha_sin_tz = timezone.make_naive(item.fecha)
        
        sheet.append([
            fecha_sin_tz, # <-- Se usa la nueva variable
            item.lote.codigo_lote,
            item.get_tipo_movimiento_display(),
            item.descripcion,
            item.cantidad_afectada
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="historial_trazabilidad.xlsx"'
    workbook.save(response)

    return response

@login_required
def dashboard_data_json(request):
    year_str = request.GET.get('year', str(timezone.now().year))
    month_str = request.GET.get('month', str(timezone.now().month))
    
    try:
        year = int(year_str)
        month = int(month_str)
    except (ValueError, TypeError):
        year = timezone.now().year
        month = timezone.now().month

    # --- 1. Datos para Progreso de Biomasa (Burbuja) ---
    lotes_activos = Lote.objects.filter(cantidad_total_peces__gt=0).exclude(etapa_actual='OVAS')
    biomasa_progreso = []
    for lote in lotes_activos:
        dias = (timezone.now().date() - lote.fecha_ingreso_etapa).days if lote.fecha_ingreso_etapa else 0
        biomasa_progreso.append({
            'lote': lote.codigo_lote,
            'etapa': lote.get_etapa_actual_display(),
            'dias': dias,
            'peso_gr': float(lote.peso_promedio_pez_gr or 0),
            'biomasa_kg': float(lote.biomasa_kg or 0),
        })
    
    # --- 2. Datos para Consumo de Alimento (Barras Apiladas) ---
    hoy = timezone.now().date()
    ayer = hoy - timedelta(days=1)
    
    consumo_hoy_map = {}
    consumo_ayer_map = {}

    # Lotes con registro de actividad HOY
    lotes_hoy = Lote.objects.filter(registros_diarios__fecha=hoy)
    for lote in lotes_hoy:
        tipo = lote.tipo_alimento
        # Acumula el consumo diario del lote en el mapa del tipo de alimento
        consumo_hoy_map[tipo] = consumo_hoy_map.get(tipo, 0) + float(lote.alimento_diario_kg)

    # Lotes con registro de actividad AYER
    lotes_ayer = Lote.objects.filter(registros_diarios__fecha=ayer)
    for lote in lotes_ayer:
        tipo = lote.tipo_alimento
        consumo_ayer_map[tipo] = consumo_ayer_map.get(tipo, 0) + float(lote.alimento_diario_kg)

    tipos_alimento = sorted(list(set(consumo_hoy_map.keys()) | set(consumo_ayer_map.keys())))
    
    consumo_alimento = {
        'labels': tipos_alimento,
        'hoy': [consumo_hoy_map.get(t, 0) for t in tipos_alimento],
        'ayer': [consumo_ayer_map.get(t, 0) for t in tipos_alimento],
    }
    
    # --- 3. Datos para Evolución de Camada (Histograma/Barras) ---
    etapas_orden = ['Ovas', 'Alevines', 'Juveniles', 'Engorde']
    camada_qs = Lote.objects.filter(cantidad_total_peces__gt=0).values('etapa_actual').annotate(total_peces=Sum('cantidad_total_peces'))
    camada_map = {c['etapa_actual']: c['total_peces'] for c in camada_qs}
    
    evolucion_camada = {
        'labels': etapas_orden,
        'data': [camada_map.get(etapa.upper(), 0) for etapa in etapas_orden]
    }

    # --- 4. Datos de Mortalidad por Lote (Barras) ---
    mortalidad_qs = Lote.objects.filter(cantidad_total_peces__gt=0).annotate(
        mortalidad_total=Coalesce(Sum('registros_mortalidad__cantidad'), 0)
    ).filter(mortalidad_total__gt=0).order_by('-mortalidad_total').values('codigo_lote', 'mortalidad_total')[:10]

    mortalidad_lotes = {
        'labels': [item['codigo_lote'] for item in mortalidad_qs],
        'data': [item['mortalidad_total'] for item in mortalidad_qs]
    }
    
    # --- Respuesta Final ---
    data = {
        'biomasa_progreso': biomasa_progreso,
        'consumo_alimento': consumo_alimento,
        'evolucion_camada': evolucion_camada,
        'mortalidad_lotes': mortalidad_lotes,
    }
    return JsonResponse(data)


@login_required
def dashboard_analitico(request):
    # Aquí va la lógica para preparar el contexto si es necesario
    return render(request, 'produccion/dashboard_analitico.html')



@login_required
def exportar_lotes_excel(request):
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    # Filtramos los lotes activos que no sean ovas
    lotes = Lote.objects.filter(etapa_actual__in=['ALEVINES', 'JUVENILES', 'ENGORDE'])
    if year:
        lotes = lotes.filter(fecha_ingreso_etapa__year=year)
    if month:
        lotes = lotes.filter(fecha_ingreso_etapa__month=month)

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Reporte de Lotes"

    headers = [
        "LOTE", "ETAPA", "FECHA", "BIOMASA (Kg)", "PROMEDIO (gr/Kg)", "PESO UNITARIO (Gr)", "TALLA UNITARIA (Cm)",
        "NUMERO TOTAL DE PECES", "% DE RAC. ALI", "CONSUMO ALIMENTO (Kg)",
        "CONV. ALIM (FCR)", "GANANCIA EN PESO (Gr)", "% MORT", "PECES MUERTOS (Unid)",
        "TIPO DE DIETA"
    ]
    sheet.append(headers)

    for lote in lotes:
        # --- LÓGICA DE MORTALIDAD CORREGIDA ---
        # Sumamos todos los registros de mortalidad para obtener el total real de bajas
        peces_muertos = lote.registros_mortalidad.aggregate(total=Coalesce(Sum('cantidad'), 0))['total']
        
        # La cantidad inicial ahora es la actual más los que murieron
        cantidad_inicial_calculada = lote.cantidad_total_peces + peces_muertos
        
        porc_mort = (peces_muertos / cantidad_inicial_calculada) * 100 if cantidad_inicial_calculada > 0 else 0
        
        # --- OTROS CÁLCULOS ---
        biomasa_kg = float(lote.biomasa_kg)
        peso_unitario_gr = float(lote.peso_promedio_pez_gr or 0)
        promedio_gr_kg = (peso_unitario_gr * 1000) / biomasa_kg if biomasa_kg > 0 else 0
        
        sheet.append([
            lote.codigo_lote,
            lote.get_etapa_actual_display(),
            lote.fecha_ingreso_etapa,
            biomasa_kg,
            round(promedio_gr_kg, 2),
            peso_unitario_gr,
            float(lote.talla_max_cm or 0),
            lote.cantidad_total_peces,
            float(lote.racion_alimentaria_porcentaje),
            float(lote.alimento_diario_kg),
            float(lote.conversion_alimenticia),
            float(lote.ganancia_en_peso_gr),
            round(porc_mort, 2), # <-- TASA DE MORTALIDAD AÑADIDA
            peces_muertos,       # <-- PECES MUERTOS CORREGIDO
            lote.tipo_alimento,
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="reporte_lotes.xlsx"'
    workbook.save(response)

    return response

class DashboardAnaliticoView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'produccion.view_dashboard' # Crea este permiso si no existe
    template_name = 'produccion/dashboard.html'

    def get(self, request, *args, **kwargs):
        context = {}

        # --- Datos para Progreso de Biomasa (Gráfico de Burbuja) ---
        # Filtramos lotes activos (ej. no finalizados, o con peces)
        lotes_activos = Lote.objects.filter(
            etapa_actual__in=['ALEVINES', 'JUVENILES', 'ENGORDE'], # O tus criterios para lotes "activos"
            cantidad_total_peces__gt=0
        ).annotate(
            dias_en_etapa=F('fecha_ingreso_etapa__date') - timezone.now().date()
        ).values(
            'codigo_lote', 'etapa_actual', 'peso_promedio_pez_gr', 'cantidad_total_peces', 'fecha_ingreso_etapa'
        )

        biomasa_progreso_data = []
        for lote in lotes_activos:
            # Calcular días en etapa (abs() para asegurar positivo si la fecha_ingreso_etapa es en el futuro por error)
            delta_dias = (timezone.now().date() - lote['fecha_ingreso_etapa']).days
            dias_en_etapa = max(0, delta_dias) # Asegura que no sea negativo

            biomasa_progreso_data.append({
                'codigo': lote['codigo_lote'],
                'etapa': lote['etapa_actual'],
                'dias_en_etapa': dias_en_etapa,
                'peso_promedio_gr': float(lote['peso_promedio_pez_gr']),
                'biomasa_kg': float((lote['cantidad_total_peces'] * lote['peso_promedio_pez_gr']) / Decimal(1000)),
                'cantidad_peces': lote['cantidad_total_peces']
            })
        context['biomasa_progreso_data'] = biomasa_progreso_data

        # --- Datos para Consumo de Alimento (Gráfico de Barras Apilado) ---
        hoy = timezone.now().date()
        ayer = hoy - timedelta(days=1)

        # Agrupar consumo por tipo de alimento para hoy
        consumo_hoy = RegistroDiario.objects.filter(
            fecha=hoy,
            lote__cantidad_total_peces__gt=0 # Solo lotes con peces
        ).annotate(
            alimento_diario_lote=F('lote__alimento_diario_kg'),
            tipo_alimento_lote=F('lote__tipo_alimento')
        ).values('tipo_alimento_lote').annotate(
            total_kg=Coalesce(Sum('alimento_diario_lote'), Decimal(0.00), output_field=DecimalField())
        ).order_by('tipo_alimento_lote')
        
        # Agrupar consumo por tipo de alimento para ayer
        consumo_ayer = RegistroDiario.objects.filter(
            fecha=ayer,
            lote__cantidad_total_peces__gt=0
        ).annotate(
            alimento_diario_lote=F('lote__alimento_diario_kg'),
            tipo_alimento_lote=F('lote__tipo_alimento')
        ).values('tipo_alimento_lote').annotate(
            total_kg=Coalesce(Sum('alimento_diario_lote'), Decimal(0.00), output_field=DecimalField())
        ).order_by('tipo_alimento_lote')

        # Formatear para el gráfico
        tipos_alimento = sorted(list(set([c['tipo_alimento_lote'] for c in consumo_hoy] + [c['tipo_alimento_lote'] for c in consumo_ayer])))
        consumo_hoy_map = {c['tipo_alimento_lote']: float(c['total_kg']) for c in consumo_hoy}
        consumo_ayer_map = {c['tipo_alimento_lote']: float(c['total_kg']) for c in consumo_ayer}

        context['consumo_alimento_data'] = {
            'labels': tipos_alimento,
            'hoy': [consumo_hoy_map.get(t, 0) for t in tipos_alimento],
            'ayer': [consumo_ayer_map.get(t, 0) for t in tipos_alimento],
        }

        # --- Datos para Evolución de Camada por Etapa (Histograma/Barras agrupadas) ---
        # Contar la cantidad de peces en cada etapa actualmente
        camada_por_etapa = Lote.objects.filter(
            cantidad_total_peces__gt=0,
            etapa_actual__in=['OVAS', 'ALEVINES', 'JUVENILES', 'ENGORDE']
        ).values('etapa_actual').annotate(
            total_peces=Coalesce(Sum('cantidad_total_peces'), 0)
        ).order_by('etapa_actual')

        context['evolucion_camada_data'] = {
            'labels': [item['etapa_actual'] for item in camada_por_etapa],
            'data': [item['total_peces'] for item in camada_por_etapa],
        }

        # --- Datos para Mortalidad por Lote (Barras) ---
        # Puedes querer mostrar la mortalidad total de los últimos 30 días, o la total de lotes activos.
        # Aquí, sumaremos la mortalidad total por lote para los lotes activos.
        mortalidad_lotes = Lote.objects.filter(
            cantidad_total_peces__gt=0 # Lotes activos
        ).annotate(
            mortalidad_total_lote=Coalesce(Sum('registros_mortalidad__cantidad'), 0)
        ).filter(
            mortalidad_total_lote__gt=0 # Solo lotes con mortalidad
        ).order_by('-mortalidad_total_lote').values('codigo_lote', 'mortalidad_total_lote')[:10] # Top 10

        context['mortalidad_lotes_data'] = {
            'labels': [item['codigo_lote'] for item in mortalidad_lotes],
            'data': [item['mortalidad_total_lote'] for item in mortalidad_lotes],
        }


        # --- Métricas Clave (Opcional) ---
        total_biomasa_produccion = Lote.objects.filter(
            cantidad_total_peces__gt=0
        ).aggregate(
            total=Coalesce(Sum(F('cantidad_total_peces') * F('peso_promedio_pez_gr') / Decimal(1000)), Decimal(0.00))
        )['total']
        
        total_ovas_produccion = Lote.objects.filter(etapa_actual='OVAS').aggregate(
            total=Coalesce(Sum('cantidad_total_peces'), 0)
        )['total']

        # FCR Promedio: Este es más complejo y requeriría un cálculo que considere alimento consumido vs biomasa ganada.
        # Por simplicidad, aquí solo usaremos la propiedad 'conversion_alimenticia' del modelo Lote,
        # pero es importante entender que es un promedio de FCRs de lotes individuales y puede no ser
        # un FCR global exacto sin datos más detallados de alimentación histórica.
        fcr_promedio = Lote.objects.filter(
            cantidad_total_peces__gt=0, # Lotes activos
            conversion_alimenticia__gt=0 # Solo lotes con FCR calculable
        ).aggregate(
            avg_fcr=Coalesce(Avg('conversion_alimenticia'), Decimal(0.00))
        )['avg_fcr']

        context['total_biomasa_produccion'] = total_biomasa_produccion
        context['total_ovas_produccion'] = total_ovas_produccion
        context['fcr_promedio'] = fcr_promedio if fcr_promedio is not None else Decimal(0.00)

        return render(request, self.template_name, context)
