from django import forms
from .models import Bastidor, Artesa, Jaula, Lote, RegistroMortalidad 

# FORMULARIOS DE UNIDADES ACTUALIZADOS
class BastidorForm(forms.ModelForm):
    class Meta:
        model = Bastidor
        fields = ['capacidad_maxima_unidades']
        labels = {'capacidad_maxima_unidades': 'Capacidad Máxima de Ovas (unidades)'}

class ArtesaForm(forms.ModelForm):
    class Meta:
        model = Artesa
        fields = ['capacidad_maxima_unidades']
        labels = {'capacidad_maxima_unidades': 'Capacidad Máxima de Alevines (unidades)'}

class JaulaForm(forms.ModelForm):
    class Meta:
        model = Jaula
        fields = ['capacidad_maxima_unidades']
        labels = {'capacidad_maxima_unidades': 'Capacidad Máxima de Peces (unidades)'}

# NUEVO FORMULARIO PARA CREAR LOTES DE OVAS
class LoteOvaCreateForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['cantidad_total_peces']
        labels = {'cantidad_total_peces': 'Cantidad de Ovas a Ingresar'}

class RegistroMortalidadForm(forms.ModelForm):
    class Meta:
        model = RegistroMortalidad
        fields = ['cantidad']