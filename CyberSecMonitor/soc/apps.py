import os
from django.apps import AppConfig

class SocConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "soc"

    def ready(self):
        # чтобы не запускалось дважды из-за приколов StatReloader
        if os.environ.get("RUN_MAIN") != "true":
            return

        from .background_generator import start_generator_once
        start_generator_once()
