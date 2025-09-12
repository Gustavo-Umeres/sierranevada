from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.db.models import F
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.db import transaction

# Import all necessary models and forms
from .models import Bastidor, Artesa, Jaula, Lote, RegistroDiario
from .forms import BastidorForm, ArtesaForm, JaulaForm, LoteOvaCreateForm, RegistroMortalidadForm, ArtesaTallaForm

class ProduccionPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='Produccion').exists()

@login_required
def welcome_view(request):
    return render(request, 'welcome.html')

@login_required
def dashboard_produccion(request):
    return render(request, 'produccion/dashboard.html')

# --- List Views ---
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

# --- CRUD Views (Fully Defined) ---
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

# --- API/JSON Views ---
@login_required
def unidad_detail_json(request, pk, tipo_unidad):
    data = {}
    unidad_model_map = {'bastidor': Bastidor, 'artesa': Artesa, 'jaula': Jaula}
    UnidadModel = unidad_model_map.get(tipo_unidad)
    if not UnidadModel: return JsonResponse({'error': 'Tipo de unidad no válido'}, status=400)
    
    unidad = get_object_or_404(UnidadModel, pk=pk)
    lote = getattr(unidad, 'lote_actual', None)
    
    data['unidad'] = {
        'id': unidad.id,
        'codigo': unidad.codigo,
        'capacidad': unidad.capacidad_maxima_unidades,
        'disponible': unidad.esta_disponible
    }
    
    if lote:
        dias_en_etapa = (timezone.now().date() - lote.fecha_ingreso_etapa).days
        registro_hoy, _ = lote.registros_diarios.get_or_create(fecha=timezone.now().date())
        
        data['lote'] = {
            'id': lote.id, 'codigo': lote.codigo_lote, 
            'cantidad': lote.cantidad_total_peces,
            'fecha_ingreso': lote.fecha_ingreso_etapa.strftime('%d/%m/%Y'),
            'alimento_diario': lote.cantidad_alimento_diario,
            'dias_en_etapa': dias_en_etapa,
            'alimentacion_hoy': registro_hoy.alimentacion_realizada,
            'limpieza_hoy': registro_hoy.limpieza_realizada,
            'talla_min_cm': lote.talla_min_cm,
            'talla_max_cm': lote.talla_max_cm,
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
                # ... (logic to create record and update lot) ...
                return JsonResponse({'success': True, 'nueva_cantidad': lote.cantidad_total_peces})
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
    
    data = [{
        'id': artesa.id,
        'codigo': str(artesa),
        'capacidad_maxima_unidades': artesa.capacidad_maxima_unidades
    } for artesa in queryset]
    return JsonResponse(data, safe=False)

@login_required
def mover_lote_a_artesa(request, lote_id, artesa_id):
    if request.method == 'POST':
        lote = get_object_or_404(Lote, pk=lote_id)
        nueva_artesa = get_object_or_404(Artesa, pk=artesa_id)
        antiguo_bastidor = lote.bastidor

        if not nueva_artesa.esta_disponible: return JsonResponse({'error': 'La artesa seleccionada ya no está disponible.'}, status=400)
        if lote.cantidad_total_peces > nueva_artesa.capacidad_maxima_unidades: return JsonResponse({'error': 'La cantidad de alevines supera la capacidad de la artesa.'}, status=400)
        
        lote.bastidor = None
        lote.artesa = nueva_artesa
        lote.etapa_actual = 'ALEVINES'
        lote.fecha_ingreso_etapa = timezone.now().date()
        lote.save()

        if antiguo_bastidor:
            antiguo_bastidor.esta_disponible = True
            antiguo_bastidor.save()
        
        nueva_artesa.esta_disponible = False
        nueva_artesa.save()

        return JsonResponse({'success': True, 'message': 'El lote ha sido movido a la artesa con éxito.'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def artesa_definir_talla_json(request, pk):
    lote = get_object_or_404(Lote, pk=pk)
    if request.method == 'POST':
        form = ArtesaTallaForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Datos inválidos', 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def listar_jaulas_disponibles_json(request):
    jaulas = Jaula.objects.filter(esta_disponible=True).values('id', 'codigo', 'capacidad_maxima_unidades')
    return JsonResponse(list(jaulas), safe=False)

@login_required
def mover_lote_a_jaula(request, lote_id, jaula_id):
    if request.method == 'POST':
        lote = get_object_or_404(Lote, pk=lote_id)
        nueva_jaula = get_object_or_404(Jaula, pk=jaula_id)
        antigua_artesa = lote.artesa

        if not nueva_jaula.esta_disponible: return JsonResponse({'error': 'La jaula seleccionada ya no está disponible.'}, status=400)
        if lote.cantidad_total_peces > nueva_jaula.capacidad_maxima_unidades: return JsonResponse({'error': 'La cantidad de peces supera la capacidad de la jaula.'}, status=400)
        
        lote.artesa = None
        lote.jaula = nueva_jaula
        lote.etapa_actual = 'ENGORDE'
        lote.fecha_ingreso_etapa = timezone.now().date()
        lote.save()

        if antigua_artesa:
            antigua_artesa.esta_disponible = True
            antigua_artesa.save()
        
        nueva_jaula.esta_disponible = False
        nueva_jaula.save()

        return JsonResponse({'success': True, 'message': 'El lote ha sido movido a la jaula con éxito.'})
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
        artesa_destino.esta_disponible = False
        artesa_destino.save()
        
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
        jaula_destino.esta_disponible = False
        jaula_destino.save()
        
        return JsonResponse({'success': True, 'message': f'{cantidad} peces reasignados al lote {nuevo_lote.codigo_lote}.'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)