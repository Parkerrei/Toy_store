from django.db.models.signals import post_delete
from django.dispatch import  receiver 
from django.db import connection
from .models import Cart_item

@receiver(post_delete,sender=Cart_item)
def reset_cart_sequence(sender,**kwargs):
    #this sql checks the max id  and sets the next sequence value
    # if the table is empty it resets back to 1
    
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT setval(pg_get_serial_sequence('bon_app_Cart_item','id' ),"
            "COALESCE(max(id) , 0) + 1 , false) FROM bon_app_Cart_item;"
        )