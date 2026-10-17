import logging
from django.db import connection, transaction
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from .models import Product,CartItem
from django.db.models import F
from django.db import transaction, connection
def force_renumber_fast(sender,**kwargs):
    table = sender._meta.db_table
    seq = f"{table}_id_seq"
    
    with transaction.atomic():
        with connection.cursor() as cursor:
            # 1. Update ONLY rows where the ID doesn't match its sequential position
            # This prevents rewriting unchanged rows!
            cursor.execute(f'''
                WITH row_numbered AS (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY id) as new_id
                    FROM "{table}"
                )
                UPDATE "{table}" t
                SET id = rn.new_id
                FROM row_numbered rn
                WHERE t.id = rn.id AND t.id != rn.new_id;
            ''')
            
            # 2. Reset the sequence counter instantly
            cursor.execute(f'SELECT COALESCE(MAX(id), 0) + 1 FROM "{table}";')
            next_val = cursor.fetchone()[0]
            cursor.execute(f'ALTER SEQUENCE "{seq}" RESTART WITH {next_val};')

logger = logging.getLogger(__name__)
@receiver(user_logged_in)
def merge_anony_cart_once_logged_in(sender, request,user, **kwargs):
    """signal function to transfer session cart items to the database cart."""
    session_cart = request.session.get('anonymous_cart',{})
    if not session_cart:
        return
    try:
        with transaction.atomic():
            for product_id, session_qty in session_cart.items():
                if session_qty <= 0:
                    continue

                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    continue

                # Fetch or create the item in the user's cart
                # Replace user_cart=user with user=user depending on your CartItem definition
                cart_item, created = CartItem.objects.get_or_create(
                    user_cart=user,
                    product=product,
                    defaults={'quantity': session_qty}
                )

                if not created:
                    # If product already exists in DB cart, sum the quantities
                    cart_item.quantity = F('quantity') + session_qty
                    cart_item.save(update_fields=['quantity'])
        
        # delete parmanently anony session cart
        del request.session.get['anonymous_cart']
        request.session.modified = True  # important otherwise django will never know session was updated

    except Exception as e:
        logger.error(f"Failed to clear anonymous cart from session: {e}", exc_info=True)