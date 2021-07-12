from django.apps import AppConfig

class AwwConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aww'

    def ready(self):
        import aww.signals