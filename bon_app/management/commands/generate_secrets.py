from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key
import os 


class Command(BaseCommand):
    help = 'automatic generate django secrets'

    def handle(self, *args, **options):
        django_secret = get_random_secret_key()
        file = '.env'
        key_found = False

        if os.path.exists(file):
            with open(file, 'r') as f:
                data = f.readlines()
                
            # Loop through the list using index to update the line correctly
            for index in range(len(data)):
                # .upper() makes the check case-insensitive so it finds SECRET_KEY or secret_key
                if data[index].upper().startswith('SECRET_KEY='):
                    data[index] = f'SECRET_KEY="{django_secret}"\n'
                    key_found = True
                    break  # Stop looking once we found and changed it
            
            # If the variable wasn't in the file at all, append it to the end
            if not key_found:
                data.append(f'SECRET_KEY="{django_secret}"\n')

            # Save the updated data list back to the file
            with open(file, 'w') as Write:
                Write.writelines(data)               
                
            self.stdout.write(self.style.SUCCESS(f'django secret successfully saved to .env:\n{django_secret}'))
        else:
            # If the .env file doesn't exist at all, create it fresh
            with open(file, 'w') as write_file:
                write_file.write(f'SECRET_KEY="{django_secret}"\n')            
            self.stdout.write(self.style.SUCCESS(f'Created new .env file with secret:\n{django_secret}'))
