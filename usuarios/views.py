from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import (
    DniValidationForm, 
    SecurityAnswerForm, 
    CustomUserCreationForm, 
    CustomUserChangeForm
)
from .models import CustomUser

def recuperar_password_dni(request):
    if request.method == 'POST':
        form = DniValidationForm(request.POST)
        if form.is_valid():
            try:
                user = CustomUser.objects.get(dni=form.cleaned_data['dni'])
                if not user.pregunta_seguridad or not user.respuesta_seguridad:
                    messages.error(request, 'Este usuario no tiene configurada una pregunta de seguridad.')
                else:
                    request.session['recovery_user_id'] = user.id
                    return redirect('recuperar-password-pregunta')
            except CustomUser.DoesNotExist:
                messages.error(request, 'No se encontró un usuario con este DNI.')
    else:
        form = DniValidationForm()
    return render(request, 'registration/recuperar_password_dni.html', {'form': form})

def recuperar_password_pregunta(request):
    user_id = request.session.get('recovery_user_id')
    if not user_id:
        return redirect('recuperar-password-dni')

    user = get_object_or_404(CustomUser, id=user_id)
    if not user.pregunta_seguridad:
        messages.error(request, 'Error: El usuario no tiene una pregunta de seguridad.')
        return redirect('recuperar-password-dni')

    if request.method == 'POST':
        form = SecurityAnswerForm(request.POST)
        if form.is_valid():
            respuesta_ingresada = form.cleaned_data['respuesta'].strip().lower()
            respuesta_guardada = user.respuesta_seguridad
            
            if respuesta_guardada and respuesta_ingresada == respuesta_guardada.strip().lower():
                request.session['recovery_user_validated'] = True
                messages.success(request, 'Respuesta correcta. Ahora puedes cambiar tu contraseña.')
                return redirect('recuperar-password-reset')
            else:
                messages.error(request, 'La respuesta es incorrecta. Inténtalo de nuevo.')
    else:
        form = SecurityAnswerForm()
        
    return render(request, 'registration/recuperar_password_pregunta.html', {
        'form': form,
        'pregunta': user.pregunta_seguridad.texto
    })

def recuperar_password_reset(request):
    user_id = request.session.get('recovery_user_id')
    validated = request.session.get('recovery_user_validated')
    if not user_id or not validated:
        return redirect('recuperar-password-dni')

    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            request.session.flush()
            messages.success(request, '¡Tu contraseña ha sido cambiada con éxito! Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = SetPasswordForm(user)
    
    return render(request, 'registration/recuperar_password_reset.html', {'form': form})

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class UserListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'usuarios/user_list.html'
    context_object_name = 'usuarios'
    queryset = CustomUser.objects.order_by('username')

class UserCreateView(AdminRequiredMixin, CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'usuarios/user_form.html'
    success_url = reverse_lazy('user-list')

    def form_valid(self, form):
        messages.success(self.request, f'El usuario "{form.cleaned_data["username"]}" ha sido creado.')
        return super().form_valid(form)

class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'usuarios/user_form.html'
    success_url = reverse_lazy('user-list')

    def form_valid(self, form):
        messages.success(self.request, f'El usuario "{self.object.username}" ha sido actualizado.')
        return super().form_valid(form)

class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = CustomUser
    template_name = 'usuarios/user_confirm_delete.html'
    success_url = reverse_lazy('user-list')

    def form_valid(self, form):
        messages.success(self.request, f'El usuario "{self.object.username}" ha sido eliminado.')
        return super().form_valid(form)