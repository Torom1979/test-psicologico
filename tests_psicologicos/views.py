from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now, localtime, timedelta
from .models import TestPsicologico, SesionTest, InstruccionTest
from datetime import datetime
from django.utils import timezone
from collections import defaultdict

import random
import string
from django.http import JsonResponse

from django.utils.timezone import now, localdate, timedelta

def lista_tests(request):
    """ Vista que muestra los tests para el administrador. """
    tests = [
        {"nombre": "Wonderlic", "slug": "wonderlic"},
        {"nombre": "IC", "slug": "ic"},
        {"nombre": "BIP", "slug": "bip"},
        {"nombre": "DISC", "slug": "disc"},
        {"nombre": "Kostick", "slug": "kostick"},
        {"nombre": "Técnica", "slug": "tecnica"},
        {"nombre": "Raven", "slug": "raven"},
        {"nombre": "IPV", "slug": "ipv"},
    ]
    return render(request, "tests_psicologicos/lista_tests.html", {"tests": tests})

def generar_link_test(request, tipo_test):
    """Genera un link único aleatorio sin necesidad de RUT"""

    # Generamos un código aleatorio único
    codigo_unico = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

    # Creamos la sesión con el código único, pero SIN asignar fecha_fin todavía
    sesion = SesionTest.objects.create(
        test=tipo_test,
        usuario=request.user,
        codigo_unico=codigo_unico  # NO asignamos fecha_fin aquí
    )

    # Retornamos el link al administrador
    link = request.build_absolute_uri(f"/tests/{tipo_test}/{codigo_unico}/instrucciones/")
    return JsonResponse({"link": link})

def iniciar_test(request, tipo_test):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        rut = request.POST.get("rut")

        if nombre and rut:
            sesion, _ = SesionTest.objects.get_or_create(
                rut=rut,
                test=tipo_test,
                defaults={"nombre": nombre, "fecha_fin": now() + timedelta(minutes=30)}
            )
            return redirect('tests_psicologicos:instrucciones_test', tipo_test=tipo_test, rut=sesion.rut)

    return render(request, "tests_psicologicos/iniciar_test.html", {"tipo_test": tipo_test})

from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now, localtime
from django.db import transaction
from .models import TestPsicologico, SesionTest, InstruccionTest

from django.views.decorators.cache import never_cache
@never_cache
def test_view(request, tipo_test, codigo_unico):
    sesion = get_object_or_404(SesionTest, codigo_unico=codigo_unico)

    # 🔒 Si el test ya fue completado, siempre redirigir a agradecimiento
    if sesion.completado:
        return redirect('tests_psicologicos:agradecimiento_test')

    # ⏰ Si el tiempo expiró y aún no está marcado como completado
    if sesion.fecha_fin and now() >= sesion.fecha_fin:
        sesion.completado = True
        sesion.fecha_fin = now()
        sesion.save(update_fields=["completado", "fecha_fin"])
        return redirect('tests_psicologicos:agradecimiento_test')

    # 🧾 Verifica que los datos estén capturados
    if not sesion.nombre or not sesion.rut:
        return redirect('tests_psicologicos:captura_datos', tipo_test=tipo_test, codigo_unico=codigo_unico)

    # 🕓 Tiempo restante
    ahora = localtime(now())
    segundos_restantes = max(0, int((sesion.fecha_fin - ahora).total_seconds())) if sesion.fecha_fin else 0

    if request.method == "POST":
        respuestas_usuario = sesion.puntajes_ipv or {}
        for key, value in request.POST.items():
            if key.startswith("pregunta_"):
                try:
                    import json
                    # Soporte DISC: separa mas/menos
                    if "_mas" in key or "_menos" in key:
                        pregunta_id, tipo = key.split("_")[1], key.split("_")[2]
                        pregunta_id = int(pregunta_id)
                        if pregunta_id not in respuestas_usuario:
                            respuestas_usuario[pregunta_id] = {}
                        respuestas_usuario[pregunta_id][tipo] = value
                    else:
                        pregunta_id = int(key.replace("pregunta_", ""))
                        respuestas_usuario[pregunta_id] = json.loads(value)
                except Exception:
                    continue

        preguntas_bd = TestPsicologico.objects.filter(tipo_test=tipo_test)
        puntaje = 0

        if tipo_test != "disc":
            for pregunta in preguntas_bd:
                r_usu = respuestas_usuario.get(pregunta.id)
                r_ok = pregunta.respuesta_correcta
                if isinstance(r_usu, list):
                    if sorted(r_usu) == sorted(list(r_ok)):
                        puntaje += 1
                else:
                    if r_usu == r_ok:
                        puntaje += 1
        else:
            puntaje = sum(1 for v in respuestas_usuario.values() if "mas" in v and "menos" in v and v["mas"] != v["menos"])

        potencial = calcular_potencial(puntaje)

        # ✅ Guardar y cerrar sesión
        with transaction.atomic():
            sesion.completado = True
            sesion.puntaje = puntaje
            sesion.potencial = potencial
            sesion.puntajes_ipv = respuestas_usuario
            sesion.fecha_fin = now()
            sesion.save(update_fields=["completado", "puntaje", "potencial", "fecha_fin", "puntajes_ipv"])

        return redirect('tests_psicologicos:agradecimiento_test')

    instrucciones = InstruccionTest.objects.filter(tipo_test=tipo_test).first()
    preguntas_bd = TestPsicologico.objects.filter(tipo_test=tipo_test)
    preguntas = []

    for pregunta in preguntas_bd:
        opciones = [
            ('A', pregunta.opcion_a),
            ('B', pregunta.opcion_b),
            ('C', pregunta.opcion_c),
            ('D', pregunta.opcion_d),
            ('E', pregunta.opcion_e),
            ('F', pregunta.opcion_f)
        ]
        opciones = [op for op in opciones if op[1]]
        preguntas.append({
            'id': pregunta.id,
            'texto_pregunta': pregunta.texto_pregunta,
            'opciones': opciones
        })

    respuestas_guardadas = sesion.puntajes_ipv or {}
    request.session["codigo_unico"] = codigo_unico

    return render(request, "tests_psicologicos/test.html", {
        "tipo_test": tipo_test,
        "preguntas": preguntas,
        "tiempo_limite": segundos_restantes,
        "instrucciones": instrucciones,
        "codigo_unico": codigo_unico,
        "respuestas_guardadas": respuestas_guardadas
    })


def agradecimiento_test(request):
    """ Vista que muestra el mensaje de agradecimiento tras completar el test """
    return render(request, "tests_psicologicos/agradecimiento_test.html")


from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now, timedelta
from .models import InstruccionTest, SesionTest

def instrucciones_test(request, tipo_test, codigo_unico):
    """ Vista para mostrar las instrucciones antes del test """
    instrucciones = InstruccionTest.objects.filter(tipo_test=tipo_test).first()
    sesion = get_object_or_404(SesionTest, codigo_unico=codigo_unico)

    # 🚨 Si ya fue completado, redirige
    if sesion.completado:
        return redirect('tests_psicologicos:agradecimiento_test')

    if request.method == "POST":
        # ✅ Asignar tiempo límite si aún no está definido
        if not sesion.fecha_fin:
            tiempos_limite = {
                "wonderlic": 12,
                "raven": 30,
                "ic": 7,
                "bip": 120,
                "disc": 45,
                "kostick": 15,
                "tecnica": 30,
                "ipv": 40
            }
            minutos = tiempos_limite.get(tipo_test, 20)
            sesion.fecha_fin = now() + timedelta(minutes=minutos)
            sesion.save(update_fields=["fecha_fin"])

        # 👉 Después de aceptar las instrucciones, redirige al ingreso de RUT
        return redirect('tests_psicologicos:ingresar_rut', tipo_test=tipo_test, codigo_unico=codigo_unico)

    return render(request, "tests_psicologicos/instrucciones_test.html", {
        "tipo_test": tipo_test,
        "codigo_unico": codigo_unico,
        "instrucciones": instrucciones
    })


def captura_datos(request, tipo_test, codigo_unico):
    sesion = get_object_or_404(SesionTest, codigo_unico=codigo_unico)

    if sesion.completado:
        return redirect('tests_psicologicos:agradecimiento_test')

    if sesion.fecha_fin and now() >= sesion.fecha_fin:
        sesion.completado = True
        sesion.save(update_fields=["completado"])
        return redirect('tests_psicologicos:agradecimiento_test')

    
    from django.contrib import messages
    # 🧐 Validar si el mismo RUT y test ya fueron ingresados hoy
    if sesion.rut:
        hoy = localdate()
        existe = SesionTest.objects.filter(
            rut=sesion.rut,
            test=tipo_test,
            fecha_inicio__date=hoy
        ).exclude(pk=sesion.pk).exists()

        if existe:
            messages.info(request, "Ya registraste tus datos hoy. Serás redirigido directamente al test.")
            return redirect('tests_psicologicos:test_view', tipo_test=tipo_test, codigo_unico=codigo_unico)

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        rut = request.POST.get("rut")
        edad = request.POST.get("edad")
        sexo = request.POST.get("sexo")
        profesion = request.POST.get("profesion")
        correo = request.POST.get("correo")

        if nombre and rut and edad and sexo and profesion and correo:
            sesion.nombre = nombre
            sesion.rut = rut
            sesion.edad = int(edad)
            sesion.sexo = sexo
            sesion.profesion = profesion
            sesion.correo = correo

            if not sesion.fecha_fin:
                tiempos_limite = {
                    "wonderlic": 12, "raven": 30, "ic": 7,
                    "bip": 120, "disc": 45, "kostick": 15,
                    "tecnica": 30, "ipv": 40
                }
                tiempo_limite = tiempos_limite.get(tipo_test, 20)
                sesion.fecha_fin = now() + timedelta(minutes=tiempo_limite)

            sesion.save(update_fields=[
                "nombre", "rut", "edad", "sexo", "profesion", "correo", "fecha_fin"
            ])

            return redirect('tests_psicologicos:test_view', tipo_test=tipo_test, codigo_unico=codigo_unico)

    return render(request, "tests_psicologicos/captura_datos.html", {
        "tipo_test": tipo_test,
        "codigo_unico": codigo_unico
    })


def calcular_potencial(puntaje):
    """ Determina el potencial basado en el puntaje del test Wonderlic """
    if puntaje is None:
        return "N/A"
    elif puntaje <= 10:
        return "MUY INFERIOR"
    elif 11 <= puntaje <= 15:
        return "INFERIOR"
    elif 16 <= puntaje <= 20:
        return "INFERIOR AL T.M."
    elif 21 <= puntaje <= 25:
        return "TERMINO MEDIO"
    elif 26 <= puntaje <= 30:
        return "SUPERIOR AL T.M."
    else:
        return "SUPERIOR"

def resumen_tests(request):
    """ Vista que genera un resumen de los tests realizados """
    sesiones = SesionTest.objects.filter(usuario=request.user).order_by('-fecha_inicio')


    # 🔹 Agrupar sesiones por RUT (persona)
    participantes = defaultdict(lambda: {
        "id": None,
        "rut": None,
        "nombre": None,
        "wonderlic": {
            "ingreso": "N/A",
            "envio": "❌",
            "puntaje": 0,
            "potencial": "N/A",
            "duracion": "N/A",
            "fecha": "N/A"
        },
        "ic": {
            "ingreso": "N/A",
            "envio": "❌",
            "perfil": "N/A",
            "puntaje": 0,
            "duracion": "N/A",
            "fecha": "N/A"
        },
        "bip": {
            "ingreso": "N/A",
            "envio": "❌",
            "link_xml": None,
            "duracion": "N/A",
            "fecha": "N/A"
        },
        "disc": {
            "ingreso": "N/A",
            "envio": "❌",
            "perfil": "N/A"
        }
    })

    for sesion in sesiones:
        print(f"[DEBUG] Sesión ID {sesion.id} - fecha_inicio: {sesion.fecha_inicio}")  # ⬅️ AQUÍ
        rut = sesion.rut or f"ID-{sesion.id}"  # Si no hay RUT, usar un identificador único
        participante = participantes[rut]

        participante["id"] = sesion.id
        participante["rut"] = sesion.rut
        participante["nombre"] = sesion.nombre

        # 🔹 Calcular la duración real
        if sesion.fecha_inicio and sesion.fecha_fin:
            duracion_segundos = (sesion.fecha_fin - sesion.fecha_inicio).total_seconds()
            minutos = int(duracion_segundos // 60)
            segundos = int(duracion_segundos % 60)
            duracion_formateada = f"{minutos}m {segundos}s"
        else:
            duracion_formateada = "N/A"

        # 🔹 Si es Wonderlic, guardar datos en la clave "wonderlic"
        if sesion.test == "wonderlic":
            participante["wonderlic"] = {
                "ingreso": localtime(sesion.fecha_inicio).strftime("%H:%M") if sesion.fecha_inicio else "N/A",
                "envio": "✅" if sesion.completado else "❌",
                "puntaje": sesion.puntaje if sesion.puntaje is not None else 0,
                "potencial": sesion.potencial if sesion.potencial else "N/A",
                "duracion": duracion_formateada,
                "fecha": localtime(sesion.fecha_inicio).strftime("%d-%m-%Y") if sesion.fecha_inicio else "N/A"
            }

        # 🔹 Si es IC, guardar datos en la clave "ic"
        elif sesion.test == "ic":
            participante["ic"] = {
                "ingreso": localtime(sesion.fecha_inicio).strftime("%H:%M") if sesion.fecha_inicio else "N/A",
                "envio": "✅" if sesion.completado else "❌",
                "perfil": determinar_perfil_ic(sesion.puntaje),
                "puntaje": sesion.puntaje if sesion.puntaje is not None else 0,
                "duracion": duracion_formateada,
                "fecha": localtime(sesion.fecha_inicio).strftime("%d-%m-%Y") if sesion.fecha_inicio else "N/A"
            }

        # 🔹 Si es BIP, guardar datos en la clave "bip"
        elif sesion.test == "bip":
            participante["bip"] = {
                "ingreso": timezone.localtime(sesion.fecha_inicio).strftime("%H:%M") if sesion.fecha_inicio else "N/A",
                "envio": "✅" if sesion.completado else "❌",
                "link_xml": generar_link_bip(sesion),
                "duracion": duracion_formateada,
                "fecha": timezone.localtime(sesion.fecha_inicio).strftime("%d-%m-%Y") if sesion.fecha_inicio else "N/A"
            }

        # 🔹 Si es DISC, guardar datos en la clave "disc"
        elif sesion.test == "disc":
            participante["disc"] = {
                "ingreso": localtime(sesion.fecha_inicio).strftime("%H:%M") if sesion.fecha_inicio else "N/A",
                "envio": "✅" if sesion.completado else "❌",
                "perfil": determinar_perfil_disc(sesion.puntaje)
            }

        if sesion.test == "tecnica":
            participante["tecnica"] = {
                "ingreso": localtime(sesion.fecha_inicio).strftime("%H:%M") if sesion.fecha_inicio else "N/A",
                "inicio": localtime(sesion.fecha_inicio).strftime("%H:%M") if sesion.fecha_inicio else "N/A",
                "envio": "✅" if sesion.completado else "❌",
                "puntaje": sesion.puntaje if sesion.puntaje is not None else 0,
                "nota": calcular_nota_tecnica(sesion.puntaje),
                "duracion": duracion_formateada,  # ✅ Agregada la duración correcta
                "fecha": localtime(sesion.fecha_inicio).strftime("%d-%m-%Y") if sesion.fecha_inicio else "N/A"
            }

        elif sesion.test == "ipv":
            puntajes = sesion.puntajes_ipv or {}  # Asegura que no sea None
            participante["ipv"] = {
                "envio": "✅" if sesion.completado else "❌",
                "dgv": puntajes.get("dgv", 0),
                "r": puntajes.get("r", 0),
                "a": puntajes.get("a", 0),
                "i": puntajes.get("i", 0),
                "ii": puntajes.get("ii", 0),
                "iii": puntajes.get("iii", 0),
                "iv": puntajes.get("iv", 0),
                "v": puntajes.get("v", 0),
                "vi": puntajes.get("vi", 0),
                "vii": puntajes.get("vii", 0),
                "viii": puntajes.get("viii", 0),
                "ix": puntajes.get("ix", 0),
                "duracion": duracion_formateada,
                "fecha": localtime(sesion.fecha_inicio).strftime("%d-%m-%Y") if sesion.fecha_inicio else "N/A"
            }


    return render(request, "tests_psicologicos/resumen_tests.html", {"resumen": participantes.values()})
def determinar_perfil_disc(puntaje):
    """ Devuelve el perfil DISC basado en el puntaje """
    if puntaje is None:
        return "N/A"
    
    perfiles_disc = {
        (0, 10): "Reservado",
        (11, 20): "Sociable",
        (21, 30): "Perfeccionista",
        (31, 40): "Líder",
        (41, 50): "Estratega"
    }

    for rango, perfil in perfiles_disc.items():
        if rango[0] <= puntaje <= rango[1]:
            return perfil

    return "N/A"
def determinar_perfil_ic(puntaje):
    """ Devuelve el perfil del test IC basado en el puntaje PS """
    if puntaje is None:
        return "N/A"
    elif puntaje <= 10:
        return f"Inferior: PS = {puntaje}"
    elif 11 <= puntaje <= 49:
        return f"Regular: PS = {puntaje}"
    elif puntaje >= 50:
        return f"Adecuado: PS = {puntaje}"
    return "N/A"

import os
from django.conf import settings
import os
from django.conf import settings

def generar_link_bip(sesion):
    """Genera un link al XML del BIP basado en las respuestas de la sesión."""
    if not sesion.rut:
        return None  # No generar link si no hay RUT

    xml_filename = f"bip_{sesion.rut}.xml"
    file_path = os.path.join(settings.MEDIA_ROOT, "bip_results", xml_filename)

    # ✅ Asegurar que la carpeta `bip_results/` existe
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 🔹 Recuperar edad y sexo
    edad = sesion.edad if sesion.edad is not None else "XXX"
    sexo = "1" if sesion.sexo == "femenino" else "0" if sesion.sexo == "masculino" else "X"

    # 🔹 Recuperar las respuestas como strings
    respuestas_usuario = sesion.puntajes_ipv or {}

    # 🔹 Mapeo de letra a número
    letra_a_num = {'A': '1', 'B': '2', 'C': '3', 'D': '4', 'E': '5', 'F': '6'}

    # 🔹 Construir cadena de respuestas ordenadas
    respuestas_str = ''
    for i in range(296, 506):  # 296 a 505 inclusive
        letra = respuestas_usuario.get(str(i), 'X')
        numero = letra_a_num.get(letra, 'X')
        respuestas_str += numero

    # 🔹 Generar contenido XML
    xml_content = f"""<sujetos>
<sujeto idsujeto='{sesion.rut}' nombre='{sesion.nombre or "Desconocido"}' edad='{edad}' sexo='{sexo}' respuestas='{respuestas_str}'/>
</sujetos>"""

    # 🔹 Guardar el archivo
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    return f"{settings.MEDIA_URL}bip_results/{xml_filename}"



def calcular_nota_tecnica(puntaje):
    """ Convierte el puntaje en una nota del 1 al 7 """
    if puntaje is None:
        return "N/A"
    return round((puntaje / 30) * 6 + 1, 1)  # Escala proporcional entre 1 y 7

def finalizar_test_ipv(request, codigo_unico):
    """ Vista para finalizar el test IPV y guardar puntajes """
    sesion = SesionTest.objects.get(codigo_unico=codigo_unico)

    # Simulación de los puntajes obtenidos del formulario
    puntajes = {
        "dgv": 1,  # Cambia estos valores para pruebas
        "r": 2,
        "a": 5,
        "i": 3,
        "ii": 4,
        "iii": 5,
        "iv": 1,
        "v": 4,
        "vi": 3,
        "vii": 4,
        "viii": 10,
        "ix": 1
    }

    # ✅ Guarda los puntajes en la base de datos
    sesion.puntajes_ipv = puntajes
    sesion.completado = True
    sesion.fecha_fin = now()
    sesion.save(update_fields=["puntajes_ipv", "completado", "fecha_fin"])  # Solo actualiza estos campos

    return JsonResponse({"message": "Test IPV guardado correctamente", "puntajes": sesion.puntajes_ipv})

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
import json
@csrf_exempt
@csrf_exempt
def guardar_respuesta_ajax(request):
    if request.method == "POST":
        pregunta_id = request.POST.get("pregunta_id")
        respuesta = request.POST.get("respuesta")
        codigo_unico = request.session.get("codigo_unico")

        if not (pregunta_id and respuesta and codigo_unico):
            return HttpResponseBadRequest("Faltan datos")

        sesion = SesionTest.objects.filter(codigo_unico=codigo_unico).first()
        if not sesion:
            return HttpResponseBadRequest("Sesión no encontrada")

        puntajes = sesion.puntajes_ipv or {}
        try:
            parsed = json.loads(respuesta)
            puntajes[str(pregunta_id)] = parsed  # Guarda como lista
        except json.JSONDecodeError:
            puntajes[str(pregunta_id)] = respuesta  # Guarda como texto plano si no es JSON

        # ✅ Siempre guardar fuera del try/except
        sesion.puntajes_ipv = puntajes
        sesion.save(update_fields=["puntajes_ipv"])

        return JsonResponse({"status": "ok"})

    return HttpResponseBadRequest("Método no permitido")

def ingresar_rut(request, tipo_test, codigo_unico):
    sesion_actual = get_object_or_404(SesionTest, codigo_unico=codigo_unico)

    if request.method == "POST":
        rut = request.POST.get("rut")

        if rut:
            hoy = localdate()

            # 🔍 Buscar otra sesión del mismo día con datos completos (de cualquier test)
            sesion_completa = SesionTest.objects.filter(
                rut=rut,
                fecha_inicio__date=hoy
            ).exclude(nombre__isnull=True).exclude(nombre='').first()

            if sesion_completa:
                # ✅ Copiar los datos a la sesión actual
                sesion_actual.rut = rut
                sesion_actual.nombre = sesion_completa.nombre
                sesion_actual.edad = sesion_completa.edad
                sesion_actual.sexo = sesion_completa.sexo
                sesion_actual.profesion = sesion_completa.profesion
                sesion_actual.correo = sesion_completa.correo
                sesion_actual.save(update_fields=[
                    "rut", "nombre", "edad", "sexo", "profesion", "correo"
                ])

                return redirect('tests_psicologicos:test_view', tipo_test=tipo_test, codigo_unico=codigo_unico)

            else:
                # No encontró sesión previa con datos → guardar RUT y redirigir a formulario
                sesion_actual.rut = rut
                sesion_actual.save(update_fields=["rut"])
                return redirect('tests_psicologicos:captura_datos', tipo_test=tipo_test, codigo_unico=codigo_unico)

    return render(request, "tests_psicologicos/ingresar_rut.html", {
        "tipo_test": tipo_test,
        "codigo_unico": codigo_unico
    })