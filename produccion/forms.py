from django import forms
from .models import Bastidor, Artesa, Jaula, Lote, RegistroMortalidad

# ----------------------------------------------------------------
# FORMULARIO PARA BASTIDORES - Sin cambios
# ----------------------------------------------------------------

class BastidorForm(forms.ModelForm):
    # --- LÍNEA AÑADIDA ---
    cantidad_a_crear = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Cantidad a crear",
        required=True, # Lo hacemos requerido para la creación
        help_text="Crea múltiples bastidores con la misma capacidad."
    )

    class Meta:
        model = Bastidor
        fields = ['capacidad_maxima_unidades']
        labels = {
            'capacidad_maxima_unidades': 'Capacidad Máxima de Ovas (unidades)'
        }


class ArtesaForm(forms.ModelForm):
    cantidad_a_crear = forms.IntegerField(
        min_value=1, initial=1,
        label="Cantidad a crear", required=True,
        help_text="Crea múltiples artesas con las mismas dimensiones."
    )

    class Meta:
        model = Artesa
        fields = [
            'forma', 
            'largo_m', 'ancho_m',
            'diametro_m',
            'alto_m',
            'densidad_siembra_kg_m3', # El campo sigue aquí
            'cantidad_a_crear'
        ]
        widgets = {
            'forma': forms.Select(attrs={'id': 'id_forma_selector'}),
            # --- LÍNEA AÑADIDA: Esto oculta el campo en el HTML ---
            'densidad_siembra_kg_m3': forms.HiddenInput(),
        }

class JaulaForm(forms.ModelForm):
    cantidad_a_crear = forms.IntegerField(
        min_value=1, initial=1,
        label="Cantidad a crear", required=True,
        help_text="Crea múltiples jaulas con las mismas dimensiones."
    )
    class Meta:
        model = Jaula
        fields = [
            'tipo',
            'forma',
            'largo_m', 'ancho_m',
            'diametro_m',
            'alto_m',
            'densidad_siembra_kg_m3',
            'cantidad_a_crear'
        ]
        widgets = {
            'forma': forms.Select(attrs={'id': 'id_forma_selector'}),
            # --- LÍNEAS CORREGIDAS ---
            'tipo': forms.HiddenInput(),
            'densidad_siembra_kg_m3': forms.HiddenInput(),
        }
# ----------------------------------------------------------------
# OTROS FORMULARIOS - Sin cambios
# ----------------------------------------------------------------
class LoteOvaCreateForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['cantidad_total_peces']
        labels = {
            'cantidad_total_peces': 'Cantidad de Ovas a Ingresar'
        }

class RegistroMortalidadForm(forms.ModelForm):
    class Meta:
        model = RegistroMortalidad
        fields = ['cantidad']

class ArtesaTallaForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['talla_min_cm', 'talla_max_cm', 'peso_promedio_pez_gr']

class LoteTallaForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['talla_min_cm', 'talla_max_cm']

class LotePesoForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['peso_promedio_pez_gr']