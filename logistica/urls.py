# from django.urls import path
# from . import views

# urlpatterns = [
#     path('', views.dashboard_logistica, name='dashboard-logistica'),

#     # Inventario (Actividad 2)
#     path('inventario/', views.InsumoListView.as_view(), name='inventario-list'),
#     path('inventario/nuevo/', views.InsumoCreateView.as_view(), name='insumo-create'),
#     path('inventario/<int:pk>/editar/', views.InsumoUpdateView.as_view(), name='insumo-update'),

#     # Proveedores (Actividad 3)
#     path('proveedores/', views.ProveedorListView.as_view(), name='proveedor-list'),
#     path('proveedores/nuevo/', views.ProveedorCreateView.as_view(), name='proveedor-create'),
#     path('proveedores/<int:pk>/editar/', views.ProveedorUpdateView.as_view(), name='proveedor-update'),
#     path('proveedores/<int:pk>/eliminar/', views.ProveedorDeleteView.as_view(), name='proveedor-delete'),

#     # Órdenes de Compra (Actividad 4)
#     path('ordenes/', views.OrdenCompraListView.as_view(), name='ordencompra-list'),
#     path('ordenes/nueva/', views.OrdenCompraCreateView.as_view(), name='ordencompra-create'),
#     path('ordenes/<int:pk>/editar/', views.OrdenCompraUpdateView.as_view(), name='ordencompra-update'),
#     path('ordenes/<int:pk>/', views.OrdenCompraDetailView.as_view(), name='ordencompra-detail'),
#     path('ordenes/<int:pk>/recibir/', views.recibir_orden_compra, name='ordencompra-recibir'), # POST

#     # Movimientos (Actividad 1)
#     path('movimientos/', views.MovimientoInventarioListView.as_view(), name='movimiento-list'),
#     path('movimientos/nuevo/', views.MovimientoManualCreateView.as_view(), name='movimiento-create'),

#     # Conexión con Producción
#     path('despacho-produccion/', views.DespachoProduccionView.as_view(), name='despacho-produccion'),
# ]


# logistica/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_logistica, name='dashboard-logistica'),

    # Inventario (Actividad 2)
    path('inventario/', views.InsumoListView.as_view(), name='inventario-list'),
    path('inventario/nuevo/', views.InsumoCreateView.as_view(), name='insumo-create'),
    path('inventario/<int:pk>/editar/', views.InsumoUpdateView.as_view(), name='insumo-update'),

    # Proveedores (Actividad 3)
    path('proveedores/', views.ProveedorListView.as_view(), name='proveedor-list'),
    path('proveedores/nuevo/', views.ProveedorCreateView.as_view(), name='proveedor-create'),
    path('proveedores/<int:pk>/editar/', views.ProveedorUpdateView.as_view(), name='proveedor-update'),
    path('proveedores/<int:pk>/eliminar/', views.ProveedorDeleteView.as_view(), name='proveedor-delete'),

    # Órdenes de Compra (Actividad 4)
    path('ordenes/', views.OrdenCompraListView.as_view(), name='ordencompra-list'),
    path('ordenes/nueva/', views.OrdenCompraCreateView.as_view(), name='ordencompra-create'),
    path('ordenes/<int:pk>/editar/', views.OrdenCompraUpdateView.as_view(), name='ordencompra-update'),
    path('ordenes/<int:pk>/', views.OrdenCompraDetailView.as_view(), name='ordencompra-detail'),
    path('ordenes/<int:pk>/recibir/', views.recibir_orden_compra, name='ordencompra-recibir'), # POST

    # Movimientos (Actividad 1)
    path('movimientos/', views.MovimientoInventarioListView.as_view(), name='movimiento-list'),
    path('movimientos/nuevo/', views.MovimientoManualCreateView.as_view(), name='movimiento-create'),

    # Conexión con Producción
    path('despacho-produccion/', views.DespachoProduccionView.as_view(), name='despacho-produccion'),
    
    # ================================================================
    # 2 NUEVAS URLS PARA LOS REPORTES
    # ================================================================
    path('reporte/grafico/', views.reporte_grafico_view, name='reporte-grafico'),
    path('reporte/resumen/', views.reporte_resumen_view, name='reporte-resumen'),
    path('api/reporte/grafico/', views.api_reporte_grafico, name='api-reporte-grafico'),

    path('reporte/resumen/exportar/', views.exportar_resumen_excel, name='exportar-resumen-excel'),

]