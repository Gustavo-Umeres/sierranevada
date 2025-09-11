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

    # --- LÍNEAS ELIMINADAS ---
    # path('lote/<int:lote_id>/marcar/<str:tarea>/', views.marcar_tarea, name='marcar-tarea'),
    # path('lote/<int:lote_id>/registrar-mortalidad/', views.registrar_mortalidad, name='registrar-mortalidad'),
    
    # URLs de la API para los Pop-ups
    path('api/unidad/<str:tipo_unidad>/<int:pk>/', views.unidad_detail_json, name='unidad-detail-json'),
    path('api/lote/ova/crear/<int:bastidor_id>/', views.lote_ova_create_view, name='lote-ova-create'),
    path('api/lote/<int:lote_id>/registrar_mortalidad/', views.registrar_mortalidad_json, name='registrar-mortalidad-json'),
]