# bon_app/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_delete

class BonAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bon_app'

    def ready(self):
        # 1. Import the function inside ready() to avoid circular imports
        
        # 2. Safely get all models now that the registry is ready
        app_models = self.get_models() 
        
       
        
        import bon_app.signals
