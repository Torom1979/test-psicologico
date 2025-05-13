from django.urls import path
from . import views

urlpatterns = [
    path('crear/', views.crear_psicologo, name='crear_psicologo'),
    path('listar/', views.listar_psicologos, name='listar_psicologos'),
    path('eliminar/<int:pk>/', views.eliminar_psicologo, name='eliminar_psicologo'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
]
