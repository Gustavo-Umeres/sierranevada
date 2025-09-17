# forms.py CORREGIDO PARA MOSTRAR EL DNI

from django import forms
from django.contrib.auth.forms import UserCreationForm # UserChangeForm ya no se usa para editar
from django.contrib.auth.models import Group
from .models import CustomUser

# --- Formularios para Recuperación de Contraseña (sin cambios) ---
class DniValidationForm(forms.Form):
    dni = forms.CharField(label="DNI", max_length=8, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

class SecurityAnswerForm(forms.Form):
    respuesta = forms.CharField(label="Respuesta de Seguridad", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))


# --- Formularios para Administración de Usuarios (CORREGIDOS) ---
class CustomUserCreationForm(UserCreationForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos de Módulos"
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'dni', 'pregunta_seguridad', 'respuesta_seguridad', 'groups')
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'pregunta_seguridad': forms.Select(attrs={'class': 'form-select'}),
            'respuesta_seguridad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
        }

    def save(self, commit=True):
        user = super().save(commit=True)
        user.groups.set(self.cleaned_data.get('groups', []))
        return user


# ------------------- CAMBIO IMPORTANTE AQUÍ -------------------
# Ahora hereda de forms.ModelForm en lugar de UserChangeForm
class CustomUserChangeForm(forms.ModelForm):
# -------------------------------------------------------------
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos de Módulos"
    )
    # Ya no se necesita "password = None" porque ModelForm no lo incluye por defecto

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'dni', 'is_active', 'pregunta_seguridad', 'respuesta_seguridad', 'groups')

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'pregunta_seguridad': forms.Select(attrs={'class': 'form-select'}),
            'respuesta_seguridad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
        }