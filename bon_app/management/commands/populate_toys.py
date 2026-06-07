import os 
import random 
from django.core.management.base import BaseCommand
from django.core.files import File 
from django.utils.text import slugify 
from bon_app.models import Category,Product

class Command(BaseCommand):
    help = 'Populates the database with toy products' 
    
    def add_arguments(self,parser):
        parser.add_argument('folder_path',type = str,help='absolute path to the local image folder ')

    def handle(self , *args,**options):
        source_folder = options['folder_path']

        if not os.path.exists(source_folder):
            self.stderr.write(self.style.ERROR(f'folder does not exists:{source_folder}'))
            return 
        
        #loop through category folders 
        for category_name in os.listdir(source_folder):
            category_path = os.path.join(source_folder,category_name)

            if os.path.isdir(category_path):
                category,created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'description':f'all types of {category_name} '}
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'created category:{category_name}'))

                #loop through images inside  the category folder 
                for filename in os.listdir(category_path):
                    if filename.lower().endswith(('.jpg','.jpeg','.png','webp')):
                        product_name = os.path.splitext(filename)[0]
                        file_path = os.path.join(category_path,filename) 

                        #check if product already exists to avoid duplicates 
                        if Product.objects.filter(name=product_name).exists():
                            self.stdout.write(self.style.WARNING(f'Product {product_name}already exists'))
                            continue

                        with open(file_path,'rb') as f:
                            django_file = File(f) 
                            product = Product(
                                category=category,
                                name=product_name,
                                stock=random.randint(5,50),
                                price=random.choice([19.99,29.99,49.99])

                            )

                            #this saves the model and copies the image to your media folder automatically
                            product.image.save(filename,django_file,save=True)
                        self.stdout.write(self.style.SUCCESS(f'successfully added product:{product_name}'))
        self.stdout.write(self.style.SUCCESS('\n data population completed!'
                ))