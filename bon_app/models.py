# Create your models here.
# payments/models.py

from django.utils.text import slugify
from django.db import models

class Payment(models.Model):
    order_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400,null=True)   
    slug = models.SlugField(unique=True,blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs) 
    
    def __str__(self):
        return self.name

class Product(models.Model):
    image = models.ImageField(upload_to='media/')
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name='products')
    name = models.CharField(max_length=100)
    stock = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10,decimal_places=2)

    def __str__(self):
        return self.name
