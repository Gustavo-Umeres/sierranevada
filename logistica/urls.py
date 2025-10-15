from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_logistica, name='dashboard-logistica'),
]