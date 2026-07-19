from django.urls import path
from .views import user,sanrio_stickers,sanrio_spoon_set,pencil_pouch,user_log_in,main,buy,doormats,mofusand,neck_pillow,cry_baby,melamine_plates,big_scrun,anime_pens,jelly_bunny,log_out,all_cart_items
urlpatterns = [
                path('',user,name='user'),
                path('logged/',user_log_in,name='logged'),
                path('main/',main,name='main'),
                path('buy/',buy,name='buy'),
                path('doormats/',doormats,name='doormats'),
                path('mofusand/',mofusand,name='mofusand'),
                path('cry_baby/',cry_baby,name='cry_baby'),
                path('melamine_plates/',melamine_plates,name='melamine_plates'),
                path('jelly_bunny/',jelly_bunny,name='jelly_bunny'),
                path('big_scrun/',big_scrun,name='big_scrun'),
                path('anime_pens/',anime_pens,name='anime_pens'),
                path('log_out/',log_out,name='log_out'),
                path('all_cart_items/<int:id>/',all_cart_items,name='all_cart_items'),
                path('neck_pillow/',neck_pillow,name='neck_pillow'),
                path('pencil_pouch/',pencil_pouch,name='pencil_pouch'),
                path('sanrio_spoon_set/',sanrio_spoon_set,name='sanrio_spoon_set'),
                path('sanrio_stickers/',sanrio_stickers,name='sanrio_stickers'),
                path('all_cart_items/',all_cart_items,name='all_cart_items'),
]