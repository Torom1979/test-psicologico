from django.urls import path
from . import views

app_name = "psicologos"

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path("logout/", views.logout_view, name="logout"),
    path('crear-cuenta/', views.crear_psicologo, name='crear_psicologo'),
    path('listar-psicologos/', views.listar_psicologos, name='listar_psicologos'),
    path('editar-psicologo/<int:user_id>/', views.editar_psicologo, name='editar_psicologo'),
    path('eliminar-psicologo/<int:user_id>/', views.eliminar_psicologo, name='eliminar_psicologo'),
    path('toggle-activo/', views.toggle_activo, name='toggle_activo'),

    path('recuperar/', views.recuperar_contrasena, name='recuperar_contrasena'),
    path('verificar-codigo/', views.verificar_codigo, name='verificar_codigo'),
    path('nueva-contrasena/', views.nueva_contrasena, name='nueva_contrasena'),
]