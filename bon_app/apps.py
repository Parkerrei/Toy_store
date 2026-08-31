# bon_app/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_delete

class BonAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bon_app'

    def ready(self):
        # 1. Import the function inside ready() to avoid circular imports
        from .signals import force_renumber

        # 2. Safely get all models now that the registry is ready
        app_models = self.get_models() 
        
        # 3. Connect the signal to all models
        for model in app_models:
            post_delete.connect(
                force_renumber, # Directly use function; lambda is no longer needed since force_renumber accepts **kwargs
                sender=model,
                weak=False
            )
