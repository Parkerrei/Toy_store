from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
from .forms import UserForm,logged_in
from django.contrib.auth import authenticate,login,logout
import razorpay
from django.conf import settings
from .forms import OrderForm
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse
from .models import Category,Product,Cart_item

# from .cart import Session_Cart
# Create your views here.

def user(request):
    if request.method == 'POST':
        form  = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit= True)
            login(request,user)
            return redirect('main')
        else:
            return render(request,'user_creation.html',{'form':form})
    form = UserForm()
    return render(request,'user_creation.html',{'form':form})

def user_log_in(request):
    # Support `next` parameter so users are redirected to the originally
    # requested page after successful login.
    next_url = request.GET.get('next') or request.POST.get('next')
    if request.method == 'POST': 
        form = logged_in(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user_access = authenticate(request, username=username, password=password)
            if user_access is not None:
                login(request, user_access)
                if next_url and url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()):
                    return redirect(next_url)
                return redirect('main')
            else:
                form.add_error(None, 'Invalid username or Password')
    else:
        form = logged_in()
    return render(request, 'login.html', {'form': form, 'next': next_url})

@login_required(login_url='logged')
def main(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():   
            # Save order or send email here
            return render(request, "main.html", {"form": OrderForm(), "success": True})
    else:
        form = OrderForm()          
        all_product = Product.objects.all() 
        return render(request, "main.html", {"form": form,'all_product':all_product})
    return render(request,'main.html',{'form':form})

# payments/views.py

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
client.timeout = 200

def buy(request):
    order_amount = 50000  # amount in paise (₹500)
    order_currency = 'INR'
    order_receipt = 'order_rcptid_11'
    notes = {'Shipping address': 'Imphal, Manipur'}

    order = client.order.create(dict(amount=order_amount,
                                     currency=order_currency,
                                     receipt=order_receipt,
                                     notes=notes,
                                     payment_capture='1'))
    
    context = {
        'razorpay_key_id':settings.RAZORPAY_KEY_ID,
        'order':order
    }
    
    return render(request, "payment_interface.html", context)
    # return render(request, "payment_interface.html")

def doormats(request):
    category = Category.objects.prefetch_related('products').filter(id=4).first()
    return render(request,"doormats.html",{'category':category})

def anime_pens(request):
    category = Category.objects.prefetch_related('products').filter(id=1).first()
    return render(request,"anime_pens.html",{'category':category})

def cry_baby(request):
    category = Category.objects.prefetch_related('products').filter(id=3).first()
    return render(request,"cry_baby.html",{'category':category})

def melamine_plates(request):
    category = Category.objects.prefetch_related('products').filter(id=6).first()
    return render(request,"melamine_plates.html",{'category':category})

def mofusand(request):
    category = Category.objects.prefetch_related('products').filter(id=7).first() 
    return render(request,"mofusand.html",{'category':category})

def jelly_bunny(request):
    category = Category.objects.prefetch_related('products').filter(id=5).first() 
    return render(request,"jelly_bunny.html",{'category':category})

def big_scrun(request):
    category = Category.objects.prefetch_related('products').filter(id=2).first()
    return render(request,"big_scrun.html",{'category':category})

def neck_pillow(request):
    category = Category.objects.prefetch_related('products').filter(id=8).first()
    return render(request,"neck_pillow.html",{'category':category})

def pencil_pouch(request):
    category = Category.objects.prefetch_related('products').filter(id=9).first()
    return render(request,"pencil_pouch.html",{'category':category})

def sanrio_spoon_set(request):
    category = Category.objects.prefetch_related('products').filter(id=10).first()
    return render(request,"sanrio_spoon_set.html",{'category':category})

def sanrio_stickers(request):
    category = Category.objects.prefetch_related('products').filter(id=11).first()
    return render(request,"sanrio_stickers.html",{'category':category})

def log_out(request):
    # print('before logout:',list(request.session.items()))
    logout(request)
    # print('after logout:',list(request.session.items()))
    return redirect('logged')



@login_required # Ensures anonymous users are sent to login page
def all_cart_items(request, id):
    if request.method == 'POST':
        # 1. Safely find the toy being added
        toy = get_object_or_404(Product, id=id)
                
        # 2. Check if this toy is already in the user's cart
        cart_item, created = cart_item.objects.get_or_create(
            user=request.user,
            product=toy,
            defaults={'quantity': 1} # If it doesn't exist, create it with 1
        )
        
        # 3. If it already exists, increase the quantity by 1
        if not created:
            cart_item.quantity += 1
            cart_item.save()
            
        # 4. Fetch all cart items belonging to this user to show on the page
        user_items = cart_item.objects.filter(user=request.user)
        
        # 5. Calculate total order price dynamically
        total_price = sum(item.get_subtotal() for item in user_items)
        
        context = {
            'cart_items': user_items,
            'total_price': total_price
        }
        
        # 6. Render your template page
        return render(request, 'user_cart.html', context)
    return redirect('main') # Redirect if someone tries a GET request
    
def user_cart_items(request):
    user_items  = cart_item.objects.filter(user=request.user)
    total_price = sum(item.get_subtotal() for item in user_items) 

    context = {
        'cart_items':user_items,
        'total_price':total_price
    }
    return render(request,'all_cart.html',context)