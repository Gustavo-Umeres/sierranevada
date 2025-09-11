from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_comercializacion, name='dashboard-comercializacion'),
]