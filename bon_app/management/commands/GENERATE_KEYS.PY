from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key
import os 

class command(BaseCommand):
    help = 'Generate keys for emergency use'
    def handle(self,*args,**kwargs):
        file = os.listdir('.env')
        if not os.path.exists('.env'):
            with open('.env','w') as file:
                file.write(f'RAZORPAY_KEY_SECRET={get_random_secret_key()}')
                print('env file created and razorpay secret added')
            with open('.env','a') as file:
                key_secret = get_random_secret_key()
                file.write(f'RAZORPAY_KEY_SECRET={key_secret}')
                print('razorpay secret added to env file')
    