from django.apps import AppConfig


class BonAppConfig(AppConfig):
    name = 'bon_app'

    def ready(self):
        import bon_app.signals