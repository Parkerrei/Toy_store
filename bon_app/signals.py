from django.db import connection, transaction


def force_renumber(sender, **_kwargs):
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

   