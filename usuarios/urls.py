from django.urls import path
from .views import UserListView, UserCreateView, UserUpdateView, UserDeleteView

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('nuevo/', UserCreateView.as_view(), name='user-create'),
    path('<int:pk>/editar/', UserUpdateView.as_view(), name='user-update'),
    path('<int:pk>/eliminar/', UserDeleteView.as_view(), name='user-delete'),
]