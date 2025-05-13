from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Crea un superusuario admin si no existe"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="Donwilly",
                email="admin@example.com",
                password="admin123"
            )
            self.stdout.write(self.style.SUCCESS("Superusuario 'admin' creado"))
        else:
            self.stdout.write(self.style.WARNING("El superusuario 'admin' ya existe"))
