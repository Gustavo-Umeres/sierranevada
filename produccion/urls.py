from django.urls import path
from . import views

urlpatterns = [
    # Ruta principal del módulo
    path('', views.dashboard_produccion, name='dashboard-produccion'),
    
    # URLs de Listas
    path('ovas/', views.BastidorListView.as_view(), name='bastidor-list'),
    path('alevines/', views.ArtesaListView.as_view(), name='artesa-list'),
    path('engorde/', views.JaulaListView.as_view(), name='jaula-list'),
    
    # URLs CRUD para Bastidores (Ovas)
    path('ovas/nuevo/', views.BastidorCreateView.as_view(), name='bastidor-create'),
    path('bastidor/<int:pk>/editar/', views.BastidorUpdateView.as_view(), name='bastidor-update'),
    path('bastidor/<int:pk>/eliminar/', views.BastidorDeleteView.as_view(), name='bastidor-delete'),

    # URLs CRUD para Artesas (Alevines)
    path('alevines/nuevo/', views.ArtesaCreateView.as_view(), name='artesa-create'),
    path('artesa/<int:pk>/editar/', views.ArtesaUpdateView.as_view(), name='artesa-update'),
    path('artesa/<int:pk>/eliminar/', views.ArtesaDeleteView.as_view(), name='artesa-delete'),

    # URLs CRUD para Jaulas (Engorde)
    path('engorde/nuevo/', views.JaulaCreateView.as_view(), name='jaula-create'),
    path('jaula/<int:pk>/editar/', views.JaulaUpdateView.as_view(), name='jaula-update'),
    path('jaula/<int:pk>/eliminar/', views.JaulaDeleteView.as_view(), name='jaula-delete'),
    
    # --- URLs de la API para los Pop-ups ---
    path('api/unidad/<str:tipo_unidad>/<int:pk>/', views.unidad_detail_json, name='unidad-detail-json'),
    
    # Lógica de Ovas
    path('api/lote/ova/crear/<int:bastidor_id>/', views.lote_ova_create_view, name='lote-ova-create'),
    path('api/lote/<int:lote_id>/mover_a_artesa/<int:artesa_id>/', views.mover_lote_a_artesa, name='mover-lote-a-artesa'),
    path('api/artesas_disponibles/<int:lote_id_origen>/', views.listar_artesas_disponibles_json, name='listar-otras-artesas-disponibles'),
    
    # Lógica de Alevines
    path('api/lote/<int:pk>/definir_talla/', views.lote_definir_talla_json, name='lote-definir-talla'),
    path('api/lote/<int:pk>/definir_peso/', views.lote_definir_peso_json, name='lote-definir-peso'),
    path('api/lote/<int:lote_origen_id>/reasignar_alevines/', views.reasignar_alevines_json, name='reasignar-alevines'),
    path('api/lote/<int:lote_id>/mover_a_jaula/', views.mover_lote_a_jaula, name='mover-lote-a-jaula'),
    
    # Lógica de Engorde
    path('api/jaulas_disponibles/<int:lote_id>/', views.listar_jaulas_disponibles_json, name='listar-jaulas-disponibles'),
    path('api/jaulas_disponibles/<int:lote_id_origen>/', views.listar_otras_jaulas_disponibles_json, name='listar-otras-jaulas-disponibles'),
    path('api/lote/<int:lote_origen_id>/reasignar_engorde/', views.reasignar_engorde_json, name='reasignar-engorde'),

    # Acciones comunes
    path('api/lote/<int:lote_id>/marcar_tarea/<str:tarea>/', views.marcar_tarea_json, name='marcar-tarea-json'),
    path('api/lote/<int:lote_id>/registrar_mortalidad/', views.registrar_mortalidad_json, name='registrar-mortalidad-json'),
    path('api/notifications/', views.get_notifications_json, name='get-notifications-json'),
    
    # URLs para Control de Alimentación
    path('alimentacion/', views.AlimentacionListView.as_view(), name='alimentacion-list'),
    path('alimentacion/nuevo/', views.AlimentacionCreateView.as_view(), name='alimentacion-create'),
    path('alimentacion/<int:pk>/editar/', views.AlimentacionUpdateView.as_view(), name='alimentacion-update'),
    path('alimentacion/<int:pk>/eliminar/', views.AlimentacionDeleteView.as_view(), name='alimentacion-delete'),
    path('alimentacion/lote/<int:lote_id>/', views.alimentacion_lote_detail, name='alimentacion-lote-detail'),
    
    # APIs para alimentación
    path('api/lote/<int:lote_id>/registrar_alimentacion/', views.registrar_alimentacion_json, name='registrar-alimentacion-json'),
    path('api/lote/<int:lote_id>/historial_alimentacion/', views.historial_alimentacion_json, name='historial-alimentacion-json'),
    
    # APIs para cálculo optimizado de alimentación
    path('api/lote/<int:lote_id>/calcular_alimentacion_optimizada/', views.calcular_alimentacion_optimizada_json, name='calcular-alimentacion-optimizada-json'),
    path('api/lote/<int:lote_id>/aplicar_alimentacion_optimizada/', views.aplicar_alimentacion_optimizada_json, name='aplicar-alimentacion-optimizada-json'),

]