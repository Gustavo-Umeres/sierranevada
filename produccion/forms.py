from django import forms
from django.db import models
from .models import Bastidor, Artesa, Jaula, Lote, RegistroMortalidad, Alimentacion

class BastidorForm(forms.ModelForm):
    class Meta:
        model = Bastidor
        fields = ['capacidad_maxima_unidades']
        labels = {'capacidad_maxima_unidades': 'Capacidad Máxima de Ovas (unidades)'}

class ArtesaForm(forms.ModelForm):
    class Meta:
        model = Artesa
        fields = ['capacidad_maxima_unidades']
        labels = { 'capacidad_maxima_unidades': 'Capacidad Máxima de Alevines (unidades)' }

class JaulaForm(forms.ModelForm):
    class Meta:
        model = Jaula
        fields = ['capacidad_maxima_unidades']
        labels = {'capacidad_maxima_unidades': 'Capacidad Máxima de Peces (unidades)'}

class LoteOvaCreateForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['cantidad_total_peces']
        labels = {'cantidad_total_peces': 'Cantidad de Ovas a Ingresar'}

class RegistroMortalidadForm(forms.ModelForm):
    class Meta:
        model = RegistroMortalidad
        fields = ['cantidad']

class ArtesaTallaForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['talla_min_cm', 'talla_max_cm', 'peso_promedio_pez_gr']

# --- FORMULARIOS DE MEDICIÓN DIVIDIDOS ---
class LoteTallaForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['talla_min_cm', 'talla_max_cm']

class LotePesoForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['peso_promedio_pez_gr']

class AlimentacionForm(forms.ModelForm):
    """
    Formulario para registrar la alimentación de larvas y peces.
    """
    class Meta:
        model = Alimentacion
        fields = ['lote', 'fecha', 'hora', 'cantidad_alimento_gr', 'tipo_alimento', 'observaciones']
        widgets = {
            'lote': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'cantidad_alimento_gr': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'tipo_alimento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pellets 2mm, Artemia, etc.'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones adicionales...'}),
        }
        labels = {
            'lote': 'Lote',
            'fecha': 'Fecha de Alimentación',
            'hora': 'Hora de Alimentación',
            'cantidad_alimento_gr': 'Cantidad de Alimento (gramos)',
            'tipo_alimento': 'Tipo de Alimento',
            'observaciones': 'Observaciones',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer valores por defecto
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['fecha'].initial = timezone.now().date()
            self.fields['hora'].initial = timezone.now().time()
        
        # Filtrar lotes activos (alevines y engorde)
        from .models import Lote
        self.fields['lote'].queryset = Lote.objects.filter(
            models.Q(etapa_actual='ALEVINES') | models.Q(etapa_actual='ENGORDE')
        ).order_by('codigo_lote')
    
    def clean_cantidad_alimento_gr(self):
        cantidad = self.cleaned_data.get('cantidad_alimento_gr')
        if cantidad is not None and cantidad <= 0:
            raise forms.ValidationError('La cantidad de alimento debe ser mayor que cero.')
        return cantidad