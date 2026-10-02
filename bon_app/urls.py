from django.urls import path

from .views import signup_user,user_log_in,main_page,initiate_razorpay_checkout,user_log_out,add_to_cart,show_user_cart_items,wipe_user_cart,user_cart_order_payment,increment_item,decrement_item,category_products_view

urlpatterns = [
                path('signup_user',signup_user,name='signup_user'),
                path('logged/',user_log_in,name='logged'),
                path('',main_page,name='main_page'),
                path('initiate_razorpay_checkout/<int:productId>/',initiate_razorpay_checkout,name='initiate_razorpay_checkout'),
                path('user_log_out/',user_log_out,name='user_log_out'),
                # This single line handles category 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, etc.
                path('category_products_view/<slug:slug>/',category_products_view, name='category_products_view'),
                path('add_to_cart/<int:productId>/',add_to_cart,name='add_to_cart'),
                path('show_user_cart_items/',show_user_cart_items,name='show_user_cart_items'),
                path('wipe_user_cart/',wipe_user_cart,name='wipe_user_cart'),
                path('user_cart_order_payment/',user_cart_order_payment,name='user_cart_order_payment'),
                path('increment_item/<int:productId>/',increment_item,name='increment_item'),
                path('decrement_item/<int:productId>/',decrement_item,name='decrement_item')
]