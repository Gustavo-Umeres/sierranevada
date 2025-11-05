from django.apps import AppConfig


class LogisticaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logistica'
    
    def ready(self):
        # Importar signals cuando la app esté lista
        import logistica.signals
