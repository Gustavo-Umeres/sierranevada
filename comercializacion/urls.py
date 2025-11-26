from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_comercializacion, name="dashboard-comercializacion"),

    # Clientes
    path("clientes/", views.ClienteListView.as_view(), name="cliente-list"),
    path("clientes/nuevo/", views.ClienteCreateView.as_view(), name="cliente-create"),
    path("clientes/<int:pk>/editar/", views.ClienteUpdateView.as_view(), name="cliente-update"),

    # 1. Pedido mayorista por tonelaje
    path("pedidos-mayoristas/", views.PedidoMayoristaListView.as_view(), name="pedido-mayorista-list"),
    path("pedidos-mayoristas/nuevo/", views.PedidoMayoristaCreateView.as_view(), name="pedido-mayorista-create"),
    path("pedidos-mayoristas/<int:pk>/", views.PedidoMayoristaDetailView.as_view(), name="pedido-mayorista-detail"),
    path(
        "pedidos-mayoristas/<int:pk>/aprobar/",
        views.PedidoMayoristaAprobarView.as_view(),
        name="pedido-mayorista-aprobar",
    ),
    path(
        "pedidos-mayoristas/<int:pk>/despachar/",
        views.despachar_pedido_mayorista,
        name="pedido-mayorista-despachar",
    ),

    # 3. Venta al por menor - Punto de venta
    path("ventas-pos/", views.VentaPOSListView.as_view(), name="venta-pos-list"),
    path("ventas-pos/nueva/", views.VentaPOSCreateView.as_view(), name="venta-pos-create"),
    path("ventas-pos/<int:pk>/", views.VentaPOSDetailView.as_view(), name="venta-pos-detail"),

    # 4. Venta al por menor - por pedidos
    path("ventas-pedidos/", views.VentaPedidoListView.as_view(), name="venta-pedido-list"),
    path("ventas-pedidos/nuevo/", views.VentaPedidoCreateView.as_view(), name="venta-pedido-create"),
    path("ventas-pedidos/<int:pk>/", views.VentaPedidoDetailView.as_view(), name="venta-pedido-detail"),
    path(
        "ventas-pedidos/<int:pk>/entregado/",
        views.marcar_pedido_entregado,
        name="venta-pedido-entregado",
    ),

    # 5. Reporte de ventas por tipo de venta
    path("reporte-ventas/", views.reporte_ventas_view, name="reporte-ventas"),
]
