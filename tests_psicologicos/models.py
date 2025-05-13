from django.db import models
from django.utils.timezone import now, timedelta
import random
import string
from django.conf import settings

class TestPsicologico(models.Model):
    TIPOS_TEST = [
        ('wonderlic', 'Wonderlic'),
        ('ic', 'IC'),
        ('bip', 'BIP'),
        ('disc', 'DISC'),
        ('kostick', 'Kostick'),
        ('tecnica', 'Técnica'),
        ('raven', 'Raven'),
        ('ipv', 'IPV'),
    ]

    tipo_test = models.CharField(max_length=20, choices=TIPOS_TEST)
    texto_pregunta = models.TextField()
    opcion_a = models.CharField(max_length=255)
    opcion_b = models.CharField(max_length=255)
    opcion_c = models.CharField(max_length=255, blank=True, null=True)
    opcion_d = models.CharField(max_length=255, blank=True, null=True)
    opcion_e = models.CharField(max_length=255, blank=True, null=True)  # ✅ Nuevo campo
    opcion_f = models.CharField(max_length=255, blank=True, null=True)  # ✅ Nuevo campo
    respuesta_correcta = models.CharField(
        max_length=6,
        null=True,
        blank=True
    )


    def __str__(self):
        return f"{self.tipo_test} - {self.texto_pregunta[:50]}"


def generar_codigo():
    """ Genera un código único de 12 caracteres """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

class SesionTest(models.Model):
    """ Registra una sesión de test con un código único """
    TESTS_CHOICES = [
        ('wonderlic', 'Wonderlic'),
        ('ic', 'IC'),
        ('bip', 'BIP'),
        ('disc', 'DISC'),
        ('kostick', 'Kostick'),
        ('tecnica', 'Técnica'),
        ('raven', 'Raven'),
        ('ipv', 'IPV'),
    ]

    test = models.CharField(max_length=20, choices=TESTS_CHOICES)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    completado = models.BooleanField(default=False)
    codigo_unico = models.CharField(
        max_length=12, 
        unique=True, 
        default=generar_codigo,  # ✅ Genera un código único automáticamente
    )
    nombre = models.CharField(max_length=255, blank=True, null=True)  
    rut = models.CharField(max_length=20, blank=True, null=True)  
    edad = models.PositiveIntegerField(null=True, blank=True)
    sexo = models.CharField(max_length=10, choices=[('masculino', 'Masculino'), ('femenino', 'Femenino')], null=True, blank=True)
    profesion = models.CharField(max_length=255, null=True, blank=True)
    correo = models.EmailField(null=True, blank=True)
    # 🔹 Campos agregados
    puntaje = models.IntegerField(blank=True, null=True)  # ✅ Guarda el puntaje del test
    potencial = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        choices=[
            ("MUY INFERIOR", "MUY INFERIOR"),
            ("INFERIOR", "INFERIOR"),
            ("INFERIOR AL T.M.", "INFERIOR AL T.M."),
            ("TERMINO MEDIO", "TERMINO MEDIO"),
            ("SUPERIOR AL T.M.", "SUPERIOR AL T.M."),
            ("SUPERIOR", "SUPERIOR"),
        ]
    )
    puntajes_ipv = models.JSONField(blank=True, null=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sesiones',
        null=True,  
        blank=True
    )

    def tiempo_restante(self):
        """ Devuelve el tiempo restante en minutos """
        if self.fecha_fin:
            return max(0, (self.fecha_fin - now()).seconds // 60)
        return None

    def __str__(self):
        estado = "✅ Completado" if self.completado else "⏳ En progreso"
        return f"{self.test} - Código: {self.codigo_unico} - {estado}"
    
class InstruccionTest(models.Model):
    """ Modelo para almacenar instrucciones y ejemplos del test """
    tipo_test = models.CharField(max_length=20, unique=True)  # wonderlic, raven, etc.
    texto_instrucciones = models.TextField()  # Instrucciones generales
    ejemplo_pregunta = models.TextField()  # Ejemplo de pregunta
    ejemplo_opcion_a = models.CharField(max_length=255)
    ejemplo_opcion_b = models.CharField(max_length=255)
    ejemplo_opcion_c = models.CharField(max_length=255)
    ejemplo_opcion_d = models.CharField(max_length=255)
    respuesta_correcta = models.CharField(
    max_length=1, 
    choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
    blank=True, 
    null=True  # Permite que la respuesta pueda estar vacía
    )
    
    def __str__(self):
        return f"Instrucciones para {self.tipo_test}"  

class PreguntaWonderlic(models.Model):
    """ Modelo para las preguntas del test de Wonderlic """
    texto_pregunta = models.TextField()
    opcion_a = models.CharField(max_length=255)
    opcion_b = models.CharField(max_length=255)
    opcion_c = models.CharField(max_length=255)
    opcion_d = models.CharField(max_length=255)
    respuesta_correcta = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])

    def __str__(self):
        return f"Wonderlic - {self.texto_pregunta[:50]}"    
    
    
    
      
