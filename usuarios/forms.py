from django import forms
from django.contrib.auth.models import Group
from .models import CustomUser

# --- Formularios para Administración de Usuarios (CORREGIDOS) ---

# Heredamos de forms.ModelForm en lugar de UserCreationForm para tener control total
class CustomUserCreationForm(forms.ModelForm):
    # 1. Definimos los campos de contraseña explícitamente con sus widgets
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': ' '})
    )
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': ' '})
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos de Módulos"
    )

    class Meta:
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

    # 2. Añadimos validación para asegurar que las contraseñas coincidan
    def clean_password2(self):
        cd = self.cleaned_data
        if cd.get('password') and cd.get('password2') and cd['password'] != cd['password2']:
            raise forms.ValidationError('¡Las contraseñas no coinciden!')
        return cd.get('password2')

    # 3. Sobrescribimos el método save para encriptar la contraseña
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # Guardamos los grupos después de que el usuario ha sido guardado
            user.groups.set(self.cleaned_data.get('groups', []))
        return user


# El formulario para editar usuarios está correcto y no necesita cambios.
class CustomUserChangeForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos de Módulos"
    )

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


# --- Formularios para Recuperación de Contraseña (sin cambios) ---
class DniValidationForm(forms.Form):
    dni = forms.CharField(label="DNI", max_length=8, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

class SecurityAnswerForm(forms.Form):
    respuesta = forms.CharField(label="Respuesta de Seguridad", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))