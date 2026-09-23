from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key
import os 

class Command(BaseCommand):
    help = 'automatic generate django secrets'

    def handle(self,*args,**options):
        django_secret = get_random_secret_key()

        # append in .env file 
        file = '.env'
        if os.path.exists(file):
            with open(file, 'r')as f:
                data = f.readlines()
                
            # Loop through the list using index to update the line correctly
            for index in range(len(data)):
                if data[index].startswith('secret_key='):
                    data[index] = f'secret_key={django_secret}\n'
                    break # Stop looking once we found and changed it
            
            # Save the updated data list back to the file
            with open(file,'w') as Write:
                Write.writelines(data)               
                
            self.stdout.write(self.style.SUCCESS('django secret :\n '))
        else:
            with open(file,'w') as write_file:
                write_file.write(f'secret_key={django_secret}\n')            


