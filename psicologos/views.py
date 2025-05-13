from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm

from core.models import RegistroAcceso, Usuario

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect('psicologos:dashboard')  # 👈 aquí

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Aquí se guarda el acceso real
            RegistroAcceso.objects.create(usuario=user)

            return redirect('psicologos:dashboard')  # 👈 y aquí también

    return render(request, 'psicologos/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect("psicologos:login")

@login_required
def dashboard(request):
    return render(request, 'psicologos/dashboard.html')


def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def crear_psicologo(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST.get('email')
        password = request.POST['password']
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password,first_name=first_name, last_name=last_name)
            grupo, creado = Group.objects.get_or_create(name='psicologo')
            user.groups.add(grupo)
            messages.success(request, 'Cuenta de psicólogo creada correctamente.')
            return redirect('psicologos:listar_psicologos')  
    return render(request, 'psicologos/crear_psicologo.html')

from django.db.models import Max
from django.utils.timezone import now
from tests_psicologicos.models import SesionTest  # Asegúrate de importar
from datetime import timedelta
@login_required
@user_passes_test(is_superuser)
def listar_psicologos(request):
    grupo_psicologo = Group.objects.get(name='psicologo')
    psicologos = Usuario.objects.filter(groups=grupo_psicologo).annotate(
        ultimo_acceso=Max('accesos__fecha_acceso')
    )

    hoy = now()
    inicio_mes_actual = hoy.replace(day=1)
    inicio_mes_anterior = (inicio_mes_actual - timedelta(days=1)).replace(day=1)
    fin_mes_anterior = inicio_mes_actual - timedelta(seconds=1)

    resumen = {}

    for user in psicologos:
        total_actual = SesionTest.objects.filter(
            usuario=user,
            completado=True,
            fecha_fin__gte=inicio_mes_actual,
            fecha_fin__lte=hoy
        ).count()

        total_anterior = SesionTest.objects.filter(
            usuario=user,
            completado=True,
            fecha_fin__gte=inicio_mes_anterior,
            fecha_fin__lte=fin_mes_anterior
        ).count()

        resumen[user.id] = {
            "mes_actual": total_actual,
            "mes_anterior": total_anterior,
        }
    return render(request, 'psicologos/listar_psicologos.html', {'psicologos': psicologos, 'resumen': resumen})

from django.shortcuts import get_object_or_404
@login_required
@user_passes_test(is_superuser)
def editar_psicologo(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        nueva_clave = request.POST.get('password')
        if nueva_clave:
            user.set_password(nueva_clave)
            user.save()
            messages.success(request, 'Contraseña actualizada.')
            return redirect('psicologos:listar_psicologos')
    return render(request, 'psicologos/editar_psicologo.html', {'usuario': user})

@login_required
@user_passes_test(is_superuser)
def eliminar_psicologo(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, 'Psicólogo eliminado.')
    return redirect('psicologos:listar_psicologos')

from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
@csrf_exempt  # Solo si no usas CSRF correctamente en AJAX
@login_required
@user_passes_test(is_superuser)
def toggle_activo(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        is_active = data.get('is_active')

        try:
            user = User.objects.get(id=user_id)
            user.is_active = is_active
            user.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Usuario no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import random
import datetime

# Diccionario temporal para almacenar códigos
codigo_verificacion = {}  # clave: email, valor: {'codigo': xxx, 'expira': datetime}

def recuperar_contrasena(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = Usuario.objects.get(email=email)
            codigo = str(random.randint(100000, 999999))
            expira = timezone.now() + datetime.timedelta(minutes=2)
            codigo_verificacion[email] = {'codigo': codigo, 'expira': expira}

            send_mail(
                'Código de verificación',
                f'Tu código es: {codigo}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            request.session['recuperar_email'] = email
            return redirect('psicologos:verificar_codigo')
        except Usuario.DoesNotExist:
            return render(request, 'psicologos/recuperar_contrasena.html', {'error': 'Email no encontrado'})
    return render(request, 'psicologos/recuperar_contrasena.html')


def verificar_codigo(request):
    email = request.session.get('recuperar_email')
    if not email:
        return redirect('psicologos:recuperar_contrasena')

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo')
        datos = codigo_verificacion.get(email)

        if datos and datos['codigo'] == codigo_ingresado and timezone.now() < datos['expira']:
            return redirect('psicologos:nueva_contrasena')
        else:
            return render(request, 'psicologos/verificar_codigo.html', {'error': 'Código inválido o expirado'})
    return render(request, 'psicologos/verificar_codigo.html')


def nueva_contrasena(request):
    email = request.session.get('recuperar_email')
    if not email:
        return redirect('recuperar_contrasena')

    if request.method == 'POST':
        nueva = request.POST.get('nueva')
        confirmar = request.POST.get('confirmar')

        if nueva == confirmar:
            user = Usuario.objects.get(email=email)
            user.set_password(nueva)
            user.save()
            del request.session['recuperar_email']
            codigo_verificacion.pop(email, None)
            return redirect('psicologos:login')

        else:
            return render(request, 'psicologos/nueva_contrasena.html', {'error': 'Las contraseñas no coinciden'})
    return render(request, 'psicologos/nueva_contrasena.html')    






