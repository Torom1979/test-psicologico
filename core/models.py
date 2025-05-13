from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Usuario(AbstractUser):
    PERFIL_CHOICES = (
        ('admin', 'Administrador'),
        ('psicologo', 'Psicólogo'),
    )
    perfil = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='psicologo')

    def __str__(self):
        return f"{self.username} ({self.perfil})"
    
class RegistroAcceso(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='accesos')
    fecha_acceso = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.usuario.username} ingresó el {self.fecha_acceso.strftime('%d/%m/%Y %H:%M')}"    


