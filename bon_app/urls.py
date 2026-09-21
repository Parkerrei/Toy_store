from django.urls import path
import bon_app.views as views
from .views import user,user_log_in,main,buy,log_out,add_to_cart,user_cart_items,cart_deduct,user_cart_order_payment,increment_item,decrement_item

urlpatterns = [
                path('',user,name='user'),
                path('logged/',user_log_in,name='logged'),
                path('main/',main,name='main'),
                path('buy/<int:productId>/',buy,name='buy'),
                path('log_out/',log_out,name='log_out'),
                # This single line handles category 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, etc.
                path('category_products_view/<slug:slug>/', views.category_products_view, name='category_products_view'),
                path('add_to_cart/<int:productId>/',add_to_cart,name='add_to_cart'),
                path('user_cart_items/',user_cart_items,name='user_cart_items'),
                path('cart_deduct/',cart_deduct,name='cart_deduct'),
                path('user_cart_order_payment/',user_cart_order_payment,name='user_cart_order_payment'),
                path('increment_item/<int:id>/',increment_item,name='increment_item'),
                path('decrement_item/<int:id>/',decrement_item,name='decrement_item')
]