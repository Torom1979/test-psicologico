from django.urls import path
from .views import agradecimiento_test, captura_datos, generar_link_test, instrucciones_test, lista_tests, resumen_tests, test_view, guardar_respuesta_ajax
from .views import guardar_respuesta_ajax
from django.conf import settings
from django.conf.urls.static import static
app_name = 'tests_psicologicos'

urlpatterns = [
    path('lista/', lista_tests, name='lista_tests'),
    path('resumen/', resumen_tests, name='resumen_tests'),  # ✅ Nueva URL para el resumen general
    path('generar_link/<str:tipo_test>/', generar_link_test, name='generar_link_test'),
    path('<str:tipo_test>/<str:codigo_unico>/instrucciones/', instrucciones_test, name='instrucciones_test'),
    path('<str:tipo_test>/<str:codigo_unico>/datos/', captura_datos, name='captura_datos'),  # ✅ Nueva ruta para el formulario de datos
    path('<str:tipo_test>/<str:codigo_unico>/', test_view, name='test_view'),
    path('agradecimiento/', agradecimiento_test, name='agradecimiento_test'),
    path("guardar_respuesta_ajax/", guardar_respuesta_ajax, name="guardar_respuesta_ajax"),
]

# 🔹 Servir archivos de media solo en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    