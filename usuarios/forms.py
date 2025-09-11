from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from .models import CustomUser

# --- Formularios para Recuperación de Contraseña (sin cambios) ---
class DniValidationForm(forms.Form):
    dni = forms.CharField(label="DNI", max_length=8, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

class SecurityAnswerForm(forms.Form):
    respuesta = forms.CharField(label="Respuesta de Seguridad", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))


# --- Formularios para Administración de Usuarios (CORRECCIÓN FINAL) ---
class CustomUserCreationForm(UserCreationForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos de Módulos"
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'dni', 'is_staff', 'pregunta_seguridad', 'respuesta_seguridad', 'groups')

    # Lógica de guardado simplificada y más robusta
    def save(self, commit=True):
        user = super().save(commit=True)
        user.groups.set(self.cleaned_data.get('groups', []))
        return user


class CustomUserChangeForm(UserChangeForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos de Módulos"
    )
    password = None

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'dni', 'is_staff', 'is_active', 'pregunta_seguridad', 'respuesta_seguridad', 'groups')