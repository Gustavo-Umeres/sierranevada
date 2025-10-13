
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
# MODIFIED LINE: Added Q, ExpressionWrapper, fields
from django.db.models import F, Q, ExpressionWrapper, fields, Sum 
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.db import transaction
from datetime import time, timedelta 

from .models import Bastidor, Artesa, Jaula, Lote, RegistroDiario, RegistroMortalidad, Alimentacion
from .forms import (
    BastidorForm, ArtesaForm, JaulaForm, LoteOvaCreateForm, 
    RegistroMortalidadForm, LoteTallaForm, LotePesoForm, AlimentacionForm
)



class ProduccionPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='Produccion').exists()

@login_required
def welcome_view(request):
    return render(request, 'welcome.html')

@login_required
def dashboard_produccion(request):
    return render(request, 'produccion/dashboard.html')

class BastidorListView(ProduccionPermissionMixin, ListView):
    model = Bastidor
    template_name = 'produccion/bastidor_list.html'
    context_object_name = 'unidades'
    extra_context = {'etapa': 'Ovas'}
    def get_queryset(self):
        return Bastidor.objects.select_related('lote_actual').order_by('codigo')

class ArtesaListView(ProduccionPermissionMixin, ListView):
    model = Artesa
    template_name = 'produccion/artesa_list.html'
    context_object_name = 'unidades'
    extra_context = {'etapa': 'Alevines'}
    def get_queryset(self):
        return Artesa.objects.select_related('lote_actual').order_by('codigo')

class JaulaListView(ProduccionPermissionMixin, ListView):
    model = Jaula
    template_name = 'produccion/jaula_list.html'
    context_object_name = 'unidades'
    extra_context = {'etapa': 'Engorde'}
    def get_queryset(self):
        return Jaula.objects.select_related('lote_actual').order_by('codigo')

class BastidorCreateView(ProduccionPermissionMixin, CreateView):
    model = Bastidor
    form_class = BastidorForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('bastidor-list')
    extra_context = {'tipo_unidad': 'Bastidor'}
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"El bastidor con código '{self.object.codigo}' ha sido creado.")
        return response

class BastidorUpdateView(ProduccionPermissionMixin, UpdateView):
    model = Bastidor
    form_class = BastidorForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('bastidor-list')
    extra_context = {'tipo_unidad': 'Bastidor'}
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
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('artesa-list')
    extra_context = {'tipo_unidad': 'Artesa'}
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"La artesa con código '{self.object.codigo}' ha sido creada.")
        return response

class ArtesaUpdateView(ProduccionPermissionMixin, UpdateView):
    model = Artesa
    form_class = ArtesaForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('artesa-list')
    extra_context = {'tipo_unidad': 'Artesa'}
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
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('jaula-list')
    extra_context = {'tipo_unidad': 'Jaula'}
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"La jaula con código '{self.object.codigo}' ha sido creada.")
        return response

class JaulaUpdateView(ProduccionPermissionMixin, UpdateView):
    model = Jaula
    form_class = JaulaForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('jaula-list')
    extra_context = {'tipo_unidad': 'Jaula'}
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"La jaula con código '{self.object.codigo}' ha sido actualizada.")
        return response

class JaulaDeleteView(ProduccionPermissionMixin, DeleteView):
    model = Jaula
    template_name = 'produccion/unidad_confirm_delete.html'
    success_url = reverse_lazy('jaula-list')
    def form_valid(self, form):
        messages.success(self.request, f"La jaula '{self.object.codigo}' ha sido eliminada.")
        return super().form_valid(form)

@login_required
def unidad_detail_json(request, pk, tipo_unidad):
    data = {}
    unidad_model_map = {'bastidor': Bastidor, 'artesa': Artesa, 'jaula': Jaula}
    UnidadModel = unidad_model_map.get(tipo_unidad)
    if not UnidadModel: return JsonResponse({'error': 'Tipo de unidad no válido'}, status=400)
    
    unidad = get_object_or_404(UnidadModel, pk=pk)
    lote = getattr(unidad, 'lote_actual', None)
    
    data['unidad'] = {
        'id': unidad.id, 'codigo': unidad.codigo,
        'capacidad': unidad.capacidad_maxima_unidades,
        'disponible': unidad.esta_disponible
    }
    
    if lote:
        dias_en_etapa = (timezone.now().date() - lote.fecha_ingreso_etapa).days
        registro_hoy, _ = lote.registros_diarios.get_or_create(fecha=timezone.now().date())
        
        alimento_diario = lote.cantidad_alimento_diario_gr
        if lote.etapa_actual == 'OVAS' and dias_en_etapa >= 14 and lote.peso_promedio_pez_gr is None:
             alimento_diario = lote.cantidad_total_peces / 100

        data['lote'] = {
            'id': lote.id, 'codigo': lote.codigo_lote, 
            'cantidad': lote.cantidad_total_peces,
            'fecha_ingreso': lote.fecha_ingreso_etapa.strftime('%d/%m/%Y'),
            'alimento_diario': alimento_diario,
            'dias_en_etapa': dias_en_etapa,
            'alimentacion_hoy': registro_hoy.alimentacion_realizada,
            'limpieza_hoy': registro_hoy.limpieza_realizada,
            'talla_min_cm': lote.talla_min_cm,
            'talla_max_cm': lote.talla_max_cm,
            'peso_promedio_pez_gr': lote.peso_promedio_pez_gr,
        }
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
            lote.save() # La función save del modelo se encarga de calcular el alimento
            
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
                lote.cantidad_total_peces = F('cantidad_total_peces') - cantidad
                lote.save()
                lote.refresh_from_db()

                if lote.peso_promedio_pez_gr and lote.peso_promedio_pez_gr > 0:
                    lote.recalcular_alimento_por_biomasa()
                else:
                    lote.calcular_alimento_estandar()
                
                return JsonResponse({
                    'success': True, 
                    'nueva_cantidad': lote.cantidad_total_peces,
                    'nuevo_alimento': lote.cantidad_alimento_diario_gr
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
def listar_artesas_disponibles_json(request, lote_id_origen=None):
    queryset = Artesa.objects.filter(esta_disponible=True)
    if lote_id_origen:
        lote_origen = get_object_or_404(Lote, pk=lote_id_origen)
        if lote_origen.artesa:
            queryset = queryset.exclude(pk=lote_origen.artesa.pk)
    data = [{'id': artesa.id, 'codigo': str(artesa), 'capacidad_maxima_unidades': artesa.capacidad_maxima_unidades} for artesa in queryset]
    return JsonResponse(data, safe=False)

@login_required
def mover_lote_a_artesa(request, lote_id, artesa_id):
    if request.method == 'POST':
        lote = get_object_or_404(Lote, pk=lote_id)
        nueva_artesa = get_object_or_404(Artesa, pk=artesa_id)
        antiguo_bastidor = lote.bastidor
        if not nueva_artesa.esta_disponible: return JsonResponse({'error': 'La artesa seleccionada ya no está disponible.'}, status=400)
        if lote.cantidad_total_peces > nueva_artesa.capacidad_maxima_unidades: return JsonResponse({'error': 'La cantidad de alevines supera la capacidad de la artesa.'}, status=400)
        
        alimento_estandar = lote.cantidad_alimento_diario_gr

        lote.bastidor = None
        lote.artesa = nueva_artesa
        lote.etapa_actual = 'ALEVINES'
        lote.fecha_ingreso_etapa = timezone.now().date()
        lote.cantidad_alimento_diario_gr = alimento_estandar
        lote.save()

        if antiguo_bastidor:
            antiguo_bastidor.esta_disponible = True
            antiguo_bastidor.save()
        nueva_artesa.esta_disponible = False
        nueva_artesa.save()
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
            lote.recalcular_alimento_por_biomasa()
            return JsonResponse({'success': True, 'nuevo_alimento': lote.cantidad_alimento_diario_gr})
        else:
            return JsonResponse({'error': 'Datos inválidos', 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def listar_jaulas_disponibles_json(request, lote_id):
    lote = get_object_or_404(Lote, pk=lote_id)
    cantidad_lote = lote.cantidad_total_peces
    jaulas = Jaula.objects.filter(
        esta_disponible=True,
        capacidad_maxima_unidades__gte=cantidad_lote
    ).values('id', 'codigo', 'capacidad_maxima_unidades')
    return JsonResponse(list(jaulas), safe=False)

@login_required
@transaction.atomic
def mover_lote_a_jaula(request, lote_id):
    if request.method == 'POST':
        lote_origen = get_object_or_404(Lote, pk=lote_id)
        jaula_destino_id = request.POST.get('jaula_destino')
        try:
            cantidad = int(request.POST.get('cantidad', 0))
        except (ValueError, TypeError):
            return JsonResponse({'error': 'La cantidad debe ser un número válido.'}, status=400)

        jaula_destino = get_object_or_404(Jaula, pk=jaula_destino_id)
        antigua_artesa = lote_origen.artesa

        if cantidad <= 0 or cantidad > lote_origen.cantidad_total_peces: return JsonResponse({'error': 'La cantidad a mover es inválida.'}, status=400)
        if cantidad > jaula_destino.capacidad_maxima_unidades: return JsonResponse({'error': 'La cantidad supera la capacidad de la jaula de destino.'}, status=400)
        if not jaula_destino.esta_disponible: return JsonResponse({'error': 'La jaula de destino ya está ocupada.'}, status=400)

        if cantidad == lote_origen.cantidad_total_peces:
            lote_origen.artesa = None
            lote_origen.jaula = jaula_destino
            lote_origen.etapa_actual = 'ENGORDE'
            lote_origen.fecha_ingreso_etapa = timezone.now().date()
            lote_origen.save()
            
            if antigua_artesa:
                antigua_artesa.esta_disponible = True
                antigua_artesa.save()
            
            jaula_destino.esta_disponible = False
            jaula_destino.save()
            message = 'El lote completo ha sido movido a la jaula con éxito.'
        else:
            nuevo_lote = Lote.objects.create(
                etapa_actual='ENGORDE',
                cantidad_total_peces=cantidad,
                jaula=jaula_destino,
                talla_min_cm=lote_origen.talla_min_cm,
                talla_max_cm=lote_origen.talla_max_cm,
                peso_promedio_pez_gr=lote_origen.peso_promedio_pez_gr,
                tipo_alimento=lote_origen.tipo_alimento
            )
            lote_origen.cantidad_total_peces = F('cantidad_total_peces') - cantidad
            lote_origen.save()
            lote_origen.refresh_from_db()
            
            jaula_destino.esta_disponible = False
            jaula_destino.save()

            lote_origen.recalcular_alimento_por_biomasa()
            nuevo_lote.recalcular_alimento_por_biomasa()
            message = f'{cantidad} peces movidos al nuevo lote {nuevo_lote.codigo_lote}.'

        return JsonResponse({'success': True, 'message': message})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
@transaction.atomic
def reasignar_alevines_json(request, lote_origen_id):
    if request.method == 'POST':
        lote_origen = get_object_or_404(Lote, pk=lote_origen_id)
        artesa_destino_id = request.POST.get('artesa_destino')
        cantidad = int(request.POST.get('cantidad', 0))
        artesa_destino = get_object_or_404(Artesa, pk=artesa_destino_id)
        if cantidad <= 0 or cantidad >= lote_origen.cantidad_total_peces: return JsonResponse({'error': 'La cantidad a mover es inválida.'}, status=400)
        if cantidad > artesa_destino.capacidad_maxima_unidades: return JsonResponse({'error': 'La cantidad supera la capacidad de la artesa de destino.'}, status=400)
        if not artesa_destino.esta_disponible: return JsonResponse({'error': 'La artesa de destino ya está ocupada.'}, status=400)
        
        nuevo_lote = Lote.objects.create(etapa_actual='ALEVINES', cantidad_total_peces=cantidad, artesa=artesa_destino, peso_promedio_pez_gr=lote_origen.peso_promedio_pez_gr, tipo_alimento=lote_origen.tipo_alimento)
        lote_origen.cantidad_total_peces = F('cantidad_total_peces') - cantidad
        lote_origen.save()
        lote_origen.refresh_from_db()

        artesa_destino.esta_disponible = False
        artesa_destino.save()
        
        if lote_origen.peso_promedio_pez_gr:
            lote_origen.recalcular_alimento_por_biomasa()
            nuevo_lote.recalcular_alimento_por_biomasa()
        
        return JsonResponse({'success': True, 'message': f'{cantidad} alevines reasignados al lote {nuevo_lote.codigo_lote}.'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def listar_otras_jaulas_disponibles_json(request, lote_id_origen):
    lote_origen = get_object_or_404(Lote, pk=lote_id_origen)
    queryset = Jaula.objects.filter(esta_disponible=True)
    if lote_origen.jaula:
        queryset = queryset.exclude(pk=lote_origen.jaula.pk)
    jaulas = queryset.values('id', 'codigo', 'capacidad_maxima_unidades')
    return JsonResponse(list(jaulas), safe=False)

@login_required
@transaction.atomic
def reasignar_engorde_json(request, lote_origen_id):
    if request.method == 'POST':
        lote_origen = get_object_or_404(Lote, pk=lote_origen_id)
        jaula_destino_id = request.POST.get('jaula_destino')
        cantidad = int(request.POST.get('cantidad', 0))
        jaula_destino = get_object_or_404(Jaula, pk=jaula_destino_id)
        if cantidad <= 0 or cantidad >= lote_origen.cantidad_total_peces: return JsonResponse({'error': 'La cantidad a mover es inválida.'}, status=400)
        if cantidad > jaula_destino.capacidad_maxima_unidades: return JsonResponse({'error': 'La cantidad supera la capacidad de la jaula de destino.'}, status=400)
        if not jaula_destino.esta_disponible: return JsonResponse({'error': 'La jaula de destino ya está ocupada.'}, status=400)
        
        nuevo_lote = Lote.objects.create(etapa_actual='ENGORDE', cantidad_total_peces=cantidad, jaula=jaula_destino, talla_min_cm=lote_origen.talla_min_cm, talla_max_cm=lote_origen.talla_max_cm, peso_promedio_pez_gr=lote_origen.peso_promedio_pez_gr, tipo_alimento=lote_origen.tipo_alimento)
        lote_origen.cantidad_total_peces = F('cantidad_total_peces') - cantidad
        lote_origen.save()
        lote_origen.refresh_from_db()

        jaula_destino.esta_disponible = False
        jaula_destino.save()

        lote_origen.recalcular_alimento_por_biomasa()
        nuevo_lote.recalcular_alimento_por_biomasa()
        
        return JsonResponse({'success': True, 'message': f'{cantidad} peces reasignados al lote {nuevo_lote.codigo_lote}.'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)



@login_required
def get_notifications_json(request):
    """
    Genera y devuelve notificaciones relevantes para el usuario actual
    basado en sus grupos y el estado del sistema.
    """
    notifications = []
    now = timezone.now()
    
    # --- Notificaciones para el grupo de Producción ---
    if request.user.groups.filter(name='Produccion').exists() or request.user.is_staff:
        
        # 1. Ovas que han superado los 15 días en el bastidor
        lotes_ovas_vencidos = Lote.objects.filter(
            etapa_actual='OVAS'
        ).annotate(
            dias_en_etapa=ExpressionWrapper(now.date() - F('fecha_ingreso_etapa'), output_field=fields.DurationField())
        # --- MODIFIED LINE BELOW ---
        ).filter(dias_en_etapa__gt=timedelta(days=15))
        
        for lote in lotes_ovas_vencidos:
            notifications.append({
                'area': 'Producción',
                'message': f"El lote {lote.codigo_lote} en {lote.bastidor} ha superado los 15 días. Mover a artesa.",
                'url': reverse_lazy('bastidor-list')
            })

        # 2. Alimentación olvidada después de las 8 PM
        if now.time() >= time(20, 0): # Después de las 8:00 PM
            # Obtenemos los lotes que NO tienen un registro de alimentación hoy
            lotes_activos_sin_alimentar = Lote.objects.filter(
                Q(etapa_actual='ALEVINES') | Q(etapa_actual='ENGORDE')
            ).exclude(
                registros_diarios__fecha=now.date(),
                registros_diarios__alimentacion_realizada=True
            )
            
            for lote in lotes_activos_sin_alimentar:
                unidad = lote.artesa or lote.jaula
                url = reverse_lazy('artesa-list') if lote.artesa else reverse_lazy('jaula-list')
                notifications.append({
                    'area': 'Producción',
                    'message': f"Falta alimentar el lote {lote.codigo_lote} en {unidad}.",
                    'url': url
                })

        # 3. Alevines listos para mover a jaula
        alevines_listos = Lote.objects.filter(
            etapa_actual='ALEVINES',
            peso_promedio_pez_gr__gte=75,
            talla_max_cm__gte=15
        )
        for lote in alevines_listos:
            notifications.append({
                'area': 'Producción',
                'message': f"El lote {lote.codigo_lote} en {lote.artesa} está listo para engorde en jaula.",
                'url': reverse_lazy('artesa-list')
            })

    # --- Notificaciones para el grupo de Comercialización (y Producción/Staff) ---
    if request.user.groups.filter(name__in=['Comercializacion', 'Produccion']).exists() or request.user.is_staff:
        
        # 4. Lotes en engorde listos para la venta
        lotes_para_venta = Lote.objects.filter(
            etapa_actual='ENGORDE',
            peso_promedio_pez_gr__gte=125,
            talla_max_cm__gte=25
        )
        for lote in lotes_para_venta:
            notifications.append({
                'area': 'Producción',
                'message': f"El lote {lote.codigo_lote} en {lote.jaula} está listo para la venta.",
                'url': reverse_lazy('jaula-list')
            })

    return JsonResponse(notifications, safe=False)
    """
    Genera y devuelve notificaciones relevantes para el usuario actual
    basado en sus grupos y el estado del sistema.
    """
    notifications = []
    now = timezone.now()
    
    # --- Notificaciones para el grupo de Producción ---
    if request.user.groups.filter(name='Produccion').exists() or request.user.is_staff:
        
        # 1. Ovas que han superado los 15 días en el bastidor
        lotes_ovas_vencidos = Lote.objects.filter(
            etapa_actual='OVAS'
        ).annotate(
            dias_en_etapa=ExpressionWrapper(now.date() - F('fecha_ingreso_etapa'), output_field=fields.DurationField())
        ).filter(dias_en_etapa__days__gt=15)
        
        for lote in lotes_ovas_vencidos:
            notifications.append({
                'area': 'Producción',
                'message': f"El lote {lote.codigo_lote} en {lote.bastidor} ha superado los 15 días. Mover a artesa.",
                'url': reverse_lazy('bastidor-list')
            })

        # 2. Alimentación olvidada después de las 8 PM
        if now.time() >= time(20, 0): # Después de las 8:00 PM
            registros_hoy = RegistroDiario.objects.filter(fecha=now.date(), alimentacion_realizada=False)
            lotes_sin_alimentar = Lote.objects.filter(
                Q(etapa_actual='ALEVINES') | Q(etapa_actual='ENGORDE'),
                registros_diarios__in=registros_hoy
            )
            for lote in lotes_sin_alimentar:
                unidad = lote.artesa or lote.jaula
                url = reverse_lazy('artesa-list') if lote.artesa else reverse_lazy('jaula-list')
                notifications.append({
                    'area': 'Producción',
                    'message': f"Falta alimentar el lote {lote.codigo_lote} en {unidad}.",
                    'url': url
                })

        # 3. Alevines listos para mover a jaula
        alevines_listos = Lote.objects.filter(
            etapa_actual='ALEVINES',
            peso_promedio_pez_gr__gte=75,
            talla_max_cm__gte=15
        )
        for lote in alevines_listos:
            notifications.append({
                'area': 'Producción',
                'message': f"El lote {lote.codigo_lote} en {lote.artesa} está listo para engorde en jaula.",
                'url': reverse_lazy('artesa-list')
            })

    # --- Notificaciones para el grupo de Comercialización (y Producción/Staff) ---
    if request.user.groups.filter(name__in=['Comercializacion', 'Produccion']).exists() or request.user.is_staff:
        
        # 4. Lotes en engorde listos para la venta
        lotes_para_venta = Lote.objects.filter(
            etapa_actual='ENGORDE',
            peso_promedio_pez_gr__gte=125,
            talla_max_cm__gte=25
        )
        for lote in lotes_para_venta:
            notifications.append({
                'area': 'Comercialización',
                'message': f"El lote {lote.codigo_lote} en {lote.jaula} está listo para la venta.",
                'url': reverse_lazy('jaula-list')
            })

    return JsonResponse(notifications, safe=False)

class AlimentacionListView(ProduccionPermissionMixin, ListView):
    """
    Vista para listar todos los registros de alimentación.
    Permite filtrar por lote y fecha.
    """
    model = Alimentacion
    template_name = 'produccion/alimentacion_list.html'
    context_object_name = 'registros_alimentacion'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Alimentacion.objects.select_related('lote', 'registrado_por').order_by('-fecha', '-hora')
        
    
        lote_id = self.request.GET.get('lote')
        if lote_id:
            queryset = queryset.filter(lote_id=lote_id)
        
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lotes'] = Lote.objects.filter(
            Q(etapa_actual='ALEVINES') | Q(etapa_actual='ENGORDE')
        ).order_by('codigo_lote')
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        context['lote_seleccionado'] = self.request.GET.get('lote', '')
        return context

class AlimentacionCreateView(ProduccionPermissionMixin, CreateView):
    """
    Vista para crear un nuevo registro de alimentación.
    """
    model = Alimentacion
    form_class = AlimentacionForm
    template_name = 'produccion/alimentacion_form.html'
    success_url = reverse_lazy('alimentacion-list')
    
    def form_valid(self, form):
        form.instance.registrado_por = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f"Registro de alimentación guardado exitosamente para el lote {form.instance.lote.codigo_lote}."
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lotes'] = Lote.objects.filter(
            Q(etapa_actual='ALEVINES') | Q(etapa_actual='ENGORDE')
        ).order_by('codigo_lote')
        return context

class AlimentacionUpdateView(ProduccionPermissionMixin, UpdateView):
    """
    Vista para editar un registro de alimentación existente.
    """
    model = Alimentacion
    form_class = AlimentacionForm
    template_name = 'produccion/alimentacion_form.html'
    success_url = reverse_lazy('alimentacion-list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f"Registro de alimentación actualizado exitosamente para el lote {form.instance.lote.codigo_lote}."
        )
        return response

class AlimentacionDeleteView(ProduccionPermissionMixin, DeleteView):
    """
    Vista para eliminar un registro de alimentación.
    """
    model = Alimentacion
    template_name = 'produccion/alimentacion_confirm_delete.html'
    success_url = reverse_lazy('alimentacion-list')
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f"Registro de alimentación eliminado exitosamente."
        )
        return super().form_valid(form)

@login_required
def alimentacion_lote_detail(request, lote_id):
    """
    Vista para mostrar el historial de alimentación de un lote específico.
    """
    lote = get_object_or_404(Lote, pk=lote_id)
    registros = Alimentacion.objects.filter(lote=lote).order_by('-fecha', '-hora')
    

    total_alimentaciones = registros.count()
    total_alimento_gr = registros.aggregate(
        total=Sum('cantidad_alimento_gr')
    )['total'] or 0
    

    dias_con_alimentacion = registros.values('fecha').distinct().count()
    promedio_diario = total_alimento_gr / dias_con_alimentacion if dias_con_alimentacion > 0 else 0
    
    context = {
        'lote': lote,
        'registros': registros,
        'total_alimentaciones': total_alimentaciones,
        'total_alimento_gr': total_alimento_gr,
        'promedio_diario': promedio_diario,
    }
    
    return render(request, 'produccion/alimentacion_lote_detail.html', context)

@login_required
def registrar_alimentacion_json(request, lote_id):
    """
    Vista AJAX para registrar alimentación desde los pop-ups de unidades.
    """
    lote = get_object_or_404(Lote, pk=lote_id)
    
    if request.method == 'POST':
        try:

            fecha = request.POST.get('fecha')
            hora = request.POST.get('hora')
            cantidad_alimento_gr = request.POST.get('cantidad_alimento_gr')
            tipo_alimento = request.POST.get('tipo_alimento')
            observaciones = request.POST.get('observaciones', '')
            
 
            print(f"DEBUG - Datos recibidos:")
            print(f"  lote_id: {lote_id}")
            print(f"  fecha: {fecha}")
            print(f"  hora: {hora}")
            print(f"  cantidad_alimento_gr: {cantidad_alimento_gr}")
            print(f"  tipo_alimento: {tipo_alimento}")
            print(f"  observaciones: {observaciones}")
            
            # Validaciones básicas
            if not fecha:
                return JsonResponse({'error': 'La fecha es obligatoria'}, status=400)
            if not hora:
                return JsonResponse({'error': 'La hora es obligatoria'}, status=400)
            if not cantidad_alimento_gr:
                return JsonResponse({'error': 'La cantidad es obligatoria'}, status=400)
            if not tipo_alimento:
                return JsonResponse({'error': 'El tipo de alimento es obligatorio'}, status=400)
            
            try:
                cantidad = float(cantidad_alimento_gr)
                if cantidad <= 0:
                    return JsonResponse({'error': 'La cantidad debe ser mayor que cero'}, status=400)
            except ValueError:
                return JsonResponse({'error': 'La cantidad debe ser un número válido'}, status=400)
            
            # Crear el registro directamente
            alimentacion = Alimentacion.objects.create(
                lote=lote,
                fecha=fecha,
                hora=hora,
                cantidad_alimento_gr=cantidad,
                tipo_alimento=tipo_alimento,
                observaciones=observaciones,
                registrado_por=request.user
            )
            
            print(f"DEBUG - Registro creado exitosamente: {alimentacion.id}")
            
            return JsonResponse({
                'success': True,
                'message': f'Alimentación registrada exitosamente: {alimentacion.cantidad_alimento_gr}g de {alimentacion.tipo_alimento}',
                'fecha': str(alimentacion.fecha),
                'hora': str(alimentacion.hora),
                'cantidad': alimentacion.cantidad_alimento_gr,
                'tipo': alimentacion.tipo_alimento
            })
            
        except Exception as e:
            print(f"DEBUG - Error: {str(e)}")
            return JsonResponse({
                'error': f'Error al procesar los datos: {str(e)}'
            }, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def historial_alimentacion_json(request, lote_id):
    """
    Vista AJAX para obtener el historial de alimentación de un lote.
    """
    lote = get_object_or_404(Lote, pk=lote_id)
    registros = Alimentacion.objects.filter(lote=lote).order_by('-fecha', '-hora')[:10]
    
    data = []
    for registro in registros:
        data.append({
            'fecha': registro.fecha.strftime('%d/%m/%Y'),
            'hora': registro.hora.strftime('%H:%M'),
            'cantidad': registro.cantidad_alimento_gr,
            'tipo': registro.tipo_alimento,
            'observaciones': registro.observaciones,
            'registrado_por': registro.registrado_por.get_full_name() if registro.registrado_por else 'Usuario desconocido'
        })
    
    return JsonResponse(data, safe=False)

@login_required
def calcular_alimentacion_optimizada_json(request, lote_id):
    """
    Vista AJAX para calcular la alimentación optimizada de un lote.
    """
    lote = get_object_or_404(Lote, pk=lote_id)
    
    try:
        calculo = lote.calcular_alimentacion_optimizada()
        
        # Agregar información adicional del lote
        calculo.update({
            'lote_codigo': lote.codigo_lote,
            'cantidad_peces': lote.cantidad_total_peces,
            'peso_promedio': lote.peso_promedio_pez_gr,
            'talla_min': lote.talla_min_cm,
            'talla_max': lote.talla_max_cm,
            'etapa_actual': lote.get_etapa_actual_display(),
            'unidad': str(lote.bastidor or lote.artesa or lote.jaula or 'Sin asignar'),
            'fecha_calculo': timezone.now().strftime('%d/%m/%Y %H:%M')
        })
        
        return JsonResponse({
            'success': True,
            'calculo': calculo
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al calcular alimentación: {str(e)}'
        }, status=500)

@login_required
def aplicar_alimentacion_optimizada_json(request, lote_id):
    """
    Vista AJAX para aplicar la alimentación optimizada calculada.
    """
    lote = get_object_or_404(Lote, pk=lote_id)
    
    if request.method == 'POST':
        try:
            calculo = lote.calcular_alimentacion_optimizada()
            
            # Actualizar el lote con la nueva cantidad de alimento
            lote.cantidad_alimento_diario_gr = calculo['cantidad_gr']
            lote.tipo_alimento = calculo['tipo_alimento']
            lote.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Alimentación optimizada aplicada: {calculo["cantidad_gr"]}g de {calculo["tipo_alimento"]}',
                'nueva_cantidad': calculo['cantidad_gr'],
                'nuevo_tipo': calculo['tipo_alimento']
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al aplicar alimentación: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)