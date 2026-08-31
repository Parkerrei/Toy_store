from django.db.models.signals import post_delete
from django.dispatch import  receiver 
from django.db import connection,transaction
from .models import CartItem
from django.apps import apps


def force_renumber(sender,**kwargs):
    #this sql checks the max id  and sets the next sequence value
    # if the table is empty it resets back to 1
    table = sender._meta.db_table
    seq = f"{table}_id_seq"
    with transaction.atomic():
        with connection.cursor() as cursor:
                cursor.execute(f'SELECT id FROM "{table}" ORDER BY id')
                old_ids = [r[0] for r in cursor.fetchall()]

                if not old_ids:
                     cursor.execute(f'ALTER SEQUENCE "{seq}" RESTART WITH 1;')
                     return
                #avoid clash 
                cursor.execute(f'UPDATE "{table}"SET id = -id')

                for new_id , old_id in enumerate(old_ids , start = 1):
                     cursor.execute(
                          f'UPDATE "{table}"SET id = %s WHERE id = -%s',
                          [new_id , old_id]
                     )
                cursor.execute(f'ALTER SEQUENCE "{seq}" RESTART WITH {len(old_ids) + 1};')

    #Auto-connect to all your app models
    #change 'toys' to your app name 
    app_models = apps.get_app_config('bon_app').get_models()
    for model in app_models:
         post_delete.connect(
              lambda sender , **kwargs:force_renumber(sender),
              sender = model,
              weak = False
         )