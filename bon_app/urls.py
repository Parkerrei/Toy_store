from django.urls import path
from .views import user,user_log_in,main,buy,plushies,photo_holder,mofusand,miffy,cinnamonrol,kitty,keychain,log_out,all_cart_items
urlpatterns = [
                path('',user,name='user'),
                path('logged/',user_log_in,name='logged'),
                path('main/',main,name='main'),
                path('buy/',buy,name='buy'),
                path('plushies/',plushies,name='plushies'),
                path('photo_holder/',photo_holder,name='photo_holder'),
                path('mofusand/',mofusand,name='mofusand'),
                path('miffy/',miffy,name='miffy'),
                path('keychain/',keychain,name='keychain'),
                path('cinnamonrol/',cinnamonrol,name='cinnamonrol'),
                path('kitty/',kitty,name='kitty'),
                path('log_out/',log_out,name='log_out'),
                path('all_cart_items/<str:toy_value>/',all_cart_items,name='all_cart_items'),

]