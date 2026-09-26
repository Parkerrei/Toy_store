from django.urls import path

from .views import user,user_log_in,main,buy,log_out,add_to_cart,user_cart_items,wipe_user_cart,user_cart_order_payment,increment_item,decrement_item,category_products_view

urlpatterns = [
                path('',user,name='user'),
                path('logged/',user_log_in,name='logged'),
                path('main/',main,name='main'),
                path('buy/<int:productId>/',buy,name='buy'),
                path('log_out/',log_out,name='log_out'),
                # This single line handles category 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, etc.
                path('category_products_view/<slug:slug>/',category_products_view, name='category_products_view'),
                path('add_to_cart/<int:productId>/',add_to_cart,name='add_to_cart'),
                path('user_cart_items/',user_cart_items,name='user_cart_items'),
                path('wipe_user_cart/',wipe_user_cart,name='wipe_user_cart'),
                path('user_cart_order_payment/',user_cart_order_payment,name='user_cart_order_payment'),
                path('increment_item/<int:id>/',increment_item,name='increment_item'),
                path('decrement_item/<int:id>/',decrement_item,name='decrement_item')
]