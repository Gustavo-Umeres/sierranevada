from django.urls import path
from . import views

urlpatterns = [
    # Ruta principal del módulo
    path('', views.dashboard_produccion, name='dashboard-produccion'),
    
    # URLs de Listas de Etapas
    path('ovas/', views.BastidorListView.as_view(), name='bastidor-list'),
    path('alevines/', views.ArtesaListView.as_view(), name='artesa-list'),
    path('juveniles/', views.JuvenilListView.as_view(), name='juvenil-list'),
    path('engorde/', views.EngordeListView.as_view(), name='engorde-list'), # CORREGIDO
    
    # URLs CRUD para Bastidores (Ovas)
    path('ovas/nuevo/', views.BastidorCreateView.as_view(), name='bastidor-create'),
    path('bastidor/<int:pk>/editar/', views.BastidorUpdateView.as_view(), name='bastidor-update'),
    path('bastidor/<int:pk>/eliminar/', views.BastidorDeleteView.as_view(), name='bastidor-delete'),

    # URLs CRUD para Artesas (Alevines)
    path('alevines/nuevo/', views.ArtesaCreateView.as_view(), name='artesa-create'),
    path('artesa/<int:pk>/editar/', views.ArtesaUpdateView.as_view(), name='artesa-update'),
    path('artesa/<int:pk>/eliminar/', views.ArtesaDeleteView.as_view(), name='artesa-delete'),

    # URLs CRUD genéricas para Jaulas (sirven para Juveniles y Engorde)
    path('jaulas/nuevo/', views.JaulaCreateView.as_view(), name='jaula-create'),
    path('jaulas/<int:pk>/editar/', views.JaulaUpdateView.as_view(), name='jaula-update'),
    path('jaulas/<int:pk>/eliminar/', views.JaulaDeleteView.as_view(), name='jaula-delete'),
    
    # --- URLs de la API y Lógica de Procesos ---
    
    # API general
    path('api/unidad/<str:tipo_unidad>/<int:pk>/', views.unidad_detail_json, name='unidad-detail-json'),
    path('api/notifications/', views.get_notifications_json, name='get-notifications-json'),
    
    # API Acciones comunes para Lotes
    path('api/lote/<int:pk>/definir_talla/', views.lote_definir_talla_json, name='lote-definir-talla'),
    path('api/lote/<int:pk>/definir_peso/', views.lote_definir_peso_json, name='lote-definir-peso'),
    path('api/lote/<int:lote_id>/marcar_tarea/<str:tarea>/', views.marcar_tarea_json, name='marcar-tarea-json'),
    path('api/lote/<int:lote_id>/registrar_mortalidad/', views.registrar_mortalidad_json, name='registrar-mortalidad-json'),
    
    # API Lógica de Ovas -> Alevines
    path('api/lote/ova/crear/<int:bastidor_id>/', views.lote_ova_create_view, name='lote-ova-create'),
    path('api/lote/<int:lote_id>/mover_a_artesa/<int:artesa_id>/', views.mover_lote_a_artesa, name='mover-lote-a-artesa'),
    path('api/artesas_disponibles/<int:lote_id_origen>/', views.listar_artesas_disponibles_json, name='listar-artesas-disponibles'),
    
    # API Lógica de Alevines -> Juveniles
    path('api/lote/<int:lote_id>/mover_a_jaula/', views.mover_lote_a_jaula, name='mover-lote-a-jaula'),
    path('api/jaulas_disponibles/<int:lote_id>/', views.listar_jaulas_disponibles_json, name='listar-jaulas-disponibles'),
    path('api/lote/<int:lote_origen_id>/reasignar_alevines/', views.reasignar_alevines_json, name='reasignar-alevines'),

    # API Lógica de Juveniles -> Engorde
    path('api/lote/<int:lote_id>/mover_a_jaula_engorde/', views.mover_lote_a_jaula_engorde, name='mover-lote-a-jaula-engorde'),
    path('api/jaulas_disponibles_engorde/<int:lote_id>/', views.listar_jaulas_disponibles_engorde_json, name='listar-jaulas-engorde-disponibles'),

    # API Lógica de Reasignación en Jaulas
    path('api/otras_jaulas_disponibles/<int:lote_id_origen>/', views.listar_otras_jaulas_disponibles_json, name='listar-otras-jaulas-disponibles'),
    path('api/lote/<int:lote_origen_id>/reasignar_engorde/', views.reasignar_engorde_json, name='reasignar-engorde'),
    path('historial/', views.HistorialTrazabilidadView.as_view(), name='historial-trazabilidad'),
    path('historial/exportar/', views.exportar_historial_excel, name='exportar-historial'),
    path('api/dashboard-data/', views.dashboard_data_json, name='dashboard-data-json'),
    path('analitico/', views.dashboard_analitico, name='dashboard-analitico'),
    path('reportes/exportar-lotes/', views.exportar_lotes_excel, name='exportar-lotes-excel'),
    path('diagnostico/', views.diagnostico_experto_view, name='diagnostico-experto'),
    path('salud/diagnostico/', views.diagnostico_experto_view, name='diagnostico-experto'),
    path('salud/prediccion/', views.prediccion_salud_view, name='prediccion-salud'),
]