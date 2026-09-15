from django.urls import path
import views
from .views import user,user_log_in,main,buy,log_out,add_to_cart,user_cart_items,cart_deduct,all_cart_order,increment_item,decrement_item

urlpatterns = [
                path('',user,name='user'),
                path('logged/',user_log_in,name='logged'),
                path('main/',main,name='main'),
                path('buy/<int:id>/',buy,name='buy'),
                path('log_out/',log_out,name='log_out'),
                # This single line handles category 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, etc.
                path('category/<slug:slug>/', views.category_products_view, name='category_detail'),
                path('add_to_cart/<int:id>/',add_to_cart,name='add_to_cart'),
                path('user_cart_items/',user_cart_items,name='user_cart_items'),
                path('cart_deduct/',cart_deduct,name='cart_deduct'),
                path('all_cart_order/',all_cart_order,name='all_cart_order'),
                path('increment_item/<int:id>/',increment_item,name='increment_item'),
                path('decrement_item/<int:id>/',decrement_item,name='decrement_item')
]