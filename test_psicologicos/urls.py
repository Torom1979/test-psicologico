from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('psicologos/', include('psicologos.urls')),
    path('tests/', include('tests_psicologicos.urls')),
    path('', lambda request: redirect('psicologos:login')),  # 👈 Corregido

]
