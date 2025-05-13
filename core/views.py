from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from .forms import CrearPsicologoForm
from .models import Usuario

def es_admin(user):
    return user.is_authenticated and user.perfil == 'admin'

@login_required
@user_passes_test(es_admin)
def crear_psicologo(request):
    if request.method == 'POST':
        form = CrearPsicologoForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.perfil = 'psicologo'
            usuario.save()
            return redirect('listar_psicologos')
    else:
        form = CrearPsicologoForm()
    return render(request, 'core/crear_psicologo.html', {'form': form})

@login_required
@user_passes_test(es_admin)
def listar_psicologos(request):
    psicologos = Usuario.objects.filter(perfil='psicologo')
    return render(request, 'core/listar_psicologos.html', {'psicologos': psicologos})

@login_required
@user_passes_test(es_admin)
def eliminar_psicologo(request, pk):
    Usuario.objects.filter(pk=pk, perfil='psicologo').delete()
    return redirect('listar_psicologos')

from django.contrib.auth.views import LoginView, LogoutView

class CustomLoginView(LoginView):
    template_name = 'core/login.html'

class CustomLogoutView(LogoutView):
    next_page = '/login/'




