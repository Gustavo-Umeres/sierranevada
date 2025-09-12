from django import forms
from .models import Bastidor, Artesa, Jaula, Lote, RegistroMortalidad

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

# --- FORMULARIO CORREGIDO ---
class ArtesaTallaForm(forms.ModelForm):
    class Meta:
        model = Lote  # <-- Change Artesa to Lote
        fields = ['talla_min_cm', 'talla_max_cm']