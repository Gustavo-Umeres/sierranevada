from django.contrib import admin
from django.urls import path, include
from produccion import views as produccion_views
from usuarios import views as usuarios_views

urlpatterns = [
    # URLs de Sistema
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # --- URLS DE LA APLICACIÓN (LÓGICA CORREGIDA) ---

    # 1. La página de inicio principal apunta a la vista de bienvenida.
    path('', produccion_views.welcome_view, name='welcome'),

    # 2. Cada módulo tiene su propio prefijo claro.
    path('administracion/', include('usuarios.urls')),
    path('produccion/', include('produccion.urls')),
    path('logistica/', include('logistica.urls')), # <-- DESCOMENTA ESTA LÍNEA
    path('comercializacion/', include('comercializacion.urls')), # <-- DESCOMENTA ESTA LÍNEA

    # URLs de recuperación de contraseña
    path('accounts/recuperar/', usuarios_views.recuperar_password_dni, name='recuperar-password-dni'),
    path('accounts/recuperar/pregunta/', usuarios_views.recuperar_password_pregunta, name='recuperar-password-pregunta'),
    path('accounts/recuperar/reset/', usuarios_views.recuperar_password_reset, name='recuperar-password-reset'),
    path('salud/prediccion/', produccion_views.prediccion_salud_view, name='prediccion-salud'),

]