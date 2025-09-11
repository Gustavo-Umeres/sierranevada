from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.db.models import F
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Bastidor, Artesa, Jaula, Lote
from .forms import BastidorForm, ArtesaForm, JaulaForm, LoteOvaCreateForm, RegistroMortalidadForm

class ProduccionPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Asegura que solo usuarios con permisos de Producción o staff puedan acceder."""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='Produccion').exists()

@login_required
def welcome_view(request):
    return render(request, 'welcome.html')

@login_required
def dashboard_produccion(request):
    return render(request, 'produccion/dashboard.html')

# --- Vistas de Lista ---
class BastidorListView(ProduccionPermissionMixin, ListView):
    model = Bastidor
    template_name = 'produccion/unidad_list.html'
    context_object_name = 'unidades'
    extra_context = {'tipo_unidad': 'Bastidores', 'etapa': 'Ovas', 'tipo_unidad_slug': 'bastidor'}

class ArtesaListView(ProduccionPermissionMixin, ListView):
    model = Artesa
    template_name = 'produccion/unidad_list.html'
    context_object_name = 'unidades'
    extra_context = {'tipo_unidad': 'Artesas', 'etapa': 'Alevines', 'tipo_unidad_slug': 'artesa'}

class JaulaListView(ProduccionPermissionMixin, ListView):
    model = Jaula
    template_name = 'produccion/unidad_list.html'
    context_object_name = 'unidades'
    extra_context = {'tipo_unidad': 'Jaulas', 'etapa': 'Engorde', 'tipo_unidad_slug': 'jaula'}

# --- Vistas CRUD (Añadir, Editar, Eliminar) ---
class BastidorCreateView(ProduccionPermissionMixin, CreateView):
    model = Bastidor
    form_class = BastidorForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('bastidor-list')
    extra_context = {'tipo_unidad': 'Bastidor'}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"El bastidor con código '{self.object.codigo}' ha sido creado con éxito.")
        return response

class BastidorUpdateView(ProduccionPermissionMixin, UpdateView):
    model = Bastidor
    form_class = BastidorForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('bastidor-list')
    extra_context = {'tipo_unidad': 'Bastidor'}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"El bastidor con código '{self.object.codigo}' ha sido actualizado con éxito.")
        return response

class BastidorDeleteView(ProduccionPermissionMixin, DeleteView):
    model = Bastidor
    template_name = 'produccion/unidad_confirm_delete.html'
    success_url = reverse_lazy('bastidor-list')
    extra_context = {'tipo_unidad': 'Bastidor'}

    def form_valid(self, form):
        messages.success(self.request, f"El bastidor '{self.object.codigo}' ha sido eliminado con éxito.")
        return super().form_valid(form)

class ArtesaCreateView(ProduccionPermissionMixin, CreateView):
    model = Artesa
    form_class = ArtesaForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('artesa-list')
    extra_context = {'tipo_unidad': 'Artesa'}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"La artesa con código '{self.object.codigo}' ha sido creada con éxito.")
        return response

class ArtesaUpdateView(ProduccionPermissionMixin, UpdateView):
    model = Artesa
    form_class = ArtesaForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('artesa-list')
    extra_context = {'tipo_unidad': 'Artesa'}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"La artesa con código '{self.object.codigo}' ha sido actualizada con éxito.")
        return response

class ArtesaDeleteView(ProduccionPermissionMixin, DeleteView):
    model = Artesa
    template_name = 'produccion/unidad_confirm_delete.html'
    success_url = reverse_lazy('artesa-list')
    extra_context = {'tipo_unidad': 'Artesa'}
    
    def form_valid(self, form):
        messages.success(self.request, f"La artesa '{self.object.codigo}' ha sido eliminada con éxito.")
        return super().form_valid(form)

class JaulaCreateView(ProduccionPermissionMixin, CreateView):
    model = Jaula
    form_class = JaulaForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('jaula-list')
    extra_context = {'tipo_unidad': 'Jaula'}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"La jaula con código '{self.object.codigo}' ha sido creada con éxito.")
        return response

class JaulaUpdateView(ProduccionPermissionMixin, UpdateView):
    model = Jaula
    form_class = JaulaForm
    template_name = 'produccion/unidad_form.html'
    success_url = reverse_lazy('jaula-list')
    extra_context = {'tipo_unidad': 'Jaula'}
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"La jaula con código '{self.object.codigo}' ha sido actualizada con éxito.")
        return response

class JaulaDeleteView(ProduccionPermissionMixin, DeleteView):
    model = Jaula
    template_name = 'produccion/unidad_confirm_delete.html'
    success_url = reverse_lazy('jaula-list')
    extra_context = {'tipo_unidad': 'Jaula'}
    
    def form_valid(self, form):
        messages.success(self.request, f"La jaula '{self.object.codigo}' ha sido eliminada con éxito.")
        return super().form_valid(form)

# --- Vistas API para Pop-ups (Modales) ---
@login_required
def unidad_detail_json(request, pk, tipo_unidad):
    data = {}
    unidad_model_map = {'bastidor': Bastidor, 'artesa': Artesa, 'jaula': Jaula}
    UnidadModel = unidad_model_map.get(tipo_unidad)
    if not UnidadModel:
        return JsonResponse({'error': 'Tipo de unidad no válido'}, status=400)

    unidad = get_object_or_404(UnidadModel, pk=pk)
    lote = getattr(unidad, 'lote_actual', None)

    data['unidad'] = {
        'id': unidad.id, 'codigo': unidad.codigo,
        'capacidad': unidad.capacidad_maxima_unidades,
        'disponible': unidad.esta_disponible
    }
    if lote:
        data['lote'] = {
            'id': lote.id, 'codigo': lote.codigo_lote, 
            'cantidad': lote.cantidad_total_peces,
            'fecha_ingreso': lote.fecha_ingreso_etapa.strftime('%d/%m/%Y'),
            'alimento_diario': lote.cantidad_alimento_diario,
        }
    return JsonResponse(data)

@login_required
def lote_ova_create_view(request, bastidor_id):
    bastidor = get_object_or_404(Bastidor, pk=bastidor_id)
    if request.method == 'POST':
        form = LoteOvaCreateForm(request.POST)
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad_total_peces']
            
            if cantidad <= 0:
                return JsonResponse({'error': 'La cantidad debe ser mayor que cero.'}, status=400)
            if cantidad > bastidor.capacidad_maxima_unidades:
                return JsonResponse({'error': f"La cantidad supera la capacidad máxima del bastidor ({bastidor.capacidad_maxima_unidades})."}, status=400)
            if not bastidor.esta_disponible:
                return JsonResponse({'error': 'Este bastidor ya está ocupado.'}, status=400)

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
                registro = form.save(commit=False)
                registro.lote = lote
                registro.registrado_por = request.user
                registro.save()
                
                lote.cantidad_total_peces = F('cantidad_total_peces') - cantidad
                lote.save()
                lote.refresh_from_db()

                return JsonResponse({'success': True, 'nueva_cantidad': lote.cantidad_total_peces})
            else:
                return JsonResponse({'error': 'La cantidad es inválida.'}, status=400)
        else:
            return JsonResponse({'error': 'Dato inválido.', 'errors': form.errors}, status=400)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)