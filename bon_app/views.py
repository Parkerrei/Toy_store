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
from django.db import transaction
import json
import logging


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

client         = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
client.timeout = 200
logger = logging.getLogger(__name__)

def buy(request, id):
    if request.method != 'POST':
        return JsonResponse({'Error': 'Method not allowed'}, status=405)

    # Phase 1: Verify and Secure Stock safely
    try:
        with transaction.atomic():
            try:
                toy_to_buy = Product.objects.select_for_update().get(id=id)
            except Product.DoesNotExist:
                return JsonResponse({'Error':'Item not found'}, status=404)

            if toy_to_buy.stock <= 0:
                return JsonResponse({'Error': 'Out of stock'}, status=409)

            toy_to_buy.stock -= 1
            toy_to_buy.save()
            
            # Cache values needed for the API call before leaving transaction context
            amount_paise = toy_to_buy.round_to_paise()
            item_name = toy_to_buy.name
            item_id_str = str(toy_to_buy.id)

    except Exception as db_err:
        logger.error(f"Database error during stock deduction: {db_err}")
        return JsonResponse({'Error':'Database transaction failed'}, status=500)


    # Phase 2: Create Razorpay Order outside database lock
    try:
        order = client.order.create(data={
            'amount': amount_paise,
            'currency': 'INR',
            'notes': {
                'email':request.user.email,
                'user': request.user.username,
                'item': item_name,
                'item_id':item_id_str,
            },
            'receipt': f'rcpt_{item_id_str}',
        })

    except Exception as api_err:
        # Log the exact Razorpay API failure to your terminal console
        logger.error(f"Razorpay API failure: {api_err}")
        
        # Phase 3: Rollback stock cleanly if API failed
        try:
            with transaction.atomic():
                # Avoid select_for_update here to prevent deadlocks during failure recovery
                product_rollback = Product.objects.get(id=id)
                product_rollback.stock += 1
                product_rollback.save()
        except Exception as rollback_err:
            logger.critical(f"CRITICAL: Stock rollback failed for product {id}: {rollback_err}")
        return JsonResponse({'error':f'Payment gateway initialization failed: {str(api_err)}'}, status=500)
 
    # Phase 4: Return success data
    return JsonResponse({
        'key': settings.RAZORPAY_KEY_ID,
        'amount': order['amount'],
        'currency': order['currency'],
        'notes': order['notes'],
        'order_id': order['id'],
        'receipt': order['receipt']
    })

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))
def signature_check(request):
    if request.method != 'POST':
        return JsonResponse({'error':'method not allwed'},status=405)
    try:
        data = json.loads(request.body)
        param_dict = {
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature')
        }
        
        client.utility.verify_payment_signature(param_dict)
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({'error':'signature verification failed'},status=400)
    return JsonResponse({'success':'signature verified successfullt'},status=200)

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


@login_required 
def add_to_cart(request, id):
    # Only allow POST requests for changes
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method. Only POST is allowed.'}, status=405)
        
    # 1. Safely find the product
    try:
        toy = Product.objects.get(id=id)
    except Product.DoesNotExist:
        return JsonResponse({'error':'item not found '},status=404)
    
    # 2. Get or create the cart item
    cart_item, created = Cart_item.objects.get_or_create(
        user_cart = request.user,
        product  = toy,
        defaults = {'quantity': 1}
    )

    # 3. If it already exists, increment the quantity
    if not created:
        cart_item.quantity += 1
        cart_item.save()
 
    # 5. Return JSON data to update your frontend dynamically
    return JsonResponse({
        'success': 'Item added successfully'
    })

def user_cart_items(request):
    user_items  = Cart_item.objects.filter(user_cart=request.user)
    total_price = sum(item.get_subtotal() for item in user_items) 
   
    context = {
        'cart_items':user_items,
        'total_price':total_price
    } 
    return render(request,'all_cart.html',context)


def cart_deduct(request,id):
    if request.method != 'DELETE':
        return JsonResponse({'error':'method not allowed'},status=405)
    try:
        with transaction.atomic():
            item_exist = Product.objects.filter(id=id)
            if item_exist.exists():
                query_cart_item = Cart_item.objects.select_for_update().filter(id=id).first()
                query_cart_item.save()
                item_exist.stock += 1
                item_exist.save()
                return JsonResponse({'success':'item removed'},status=200)
            return JsonResponse({'error':'item dnt exists'})
    except Exception as e:
        return JsonResponse({'error':'something went wrong '},status=500)
                                                                                                                               



# def cart_deduct(request, id):
#     # 1. Enforce the correct HTTP method
#     if request.method != 'DELETE':
#         return JsonResponse({'error': 'Method not allowed'}, status=405)
    
#     try:
#         with transaction.atomic():
#             # 2. Fetch the SPECIFIC cart item using its ID
#             # select_for_update() locks this row for Isolation safety
#             cart_item = Cart_item.objects.select_for_update().filter(id=id).first()
            
#             if not cart_item:
#                 return JsonResponse({'error': 'Item does not exist in cart'}, status=404)
            
#             # 3. Get the specific product associated with this cart item
#             # Lock the product row too because we are modifying its stock count
#             product = Product.objects.select_for_update().get(id=cart_item.product.id)
            
#             # 4. Restore the stock (add back the quantity the user had in their cart)
#             product.stock += cart_item.quantity
#             product.save()  # Saves the specific product instance
            
#             # 5. Delete the cart item completely
#             cart_item.delete()  
            
#             return JsonResponse({'success': 'Item removed from cart'}, status=200)
            
#     except Exception as e:
#         # It's helpful to log 'e' to your console during development to debug errors
#         print(f"Error: {e}") 
#         return JsonResponse({'error': 'Something went wrong'}, status=500)

def deduct(request,id):
    if request.method !="POST":
        return JsonResponse({'error':'method not allowed'},status=405)
    try:
        with transaction.atomic():
            product = Product.objects.filter(id=id).select_for_update().first()
            if not product:
                return JsonResponse({'error':'item doesnot exist'},status=404)
            Cart_item.objects.filter(id=product).select_for_update().delete()
            product.stock += 1
            product.save()
            return JsonResponse({'success':'item stocked successfuly'},status=200)
        return JsonResponse({'error':'something went wrong'},status=500)
    except Exception as e:
        return JsonResponse({'error':'something went wrong'},status=500)
            

