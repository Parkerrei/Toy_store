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

def buy(request, id):
        if request.method == 'POST':
            try:
                with transaction.atomic:
                    try:
                         toy = Product.objects.select_for_update.get(id=id)
                    except Product.DoesNotExist:
                        return JsonResponse({'error':'item doesnot exist!'},status=404)
                    if toy.stock <= 0:
                        return JsonResponse({'error':'out of stock'},status=403)

                    toy.stock -= 1
                    toy.stock.save()

                    order = client.order.create({
                        'amount':toy.round_to_paise(),
                        'currency':'INR',
                        'receipt':f'rcpt_{toy.id}',
                        'payment_capture':True,

                        'notes':{
                        'username':request.user.username,
                        'email':request.user.email,
                        'item_name':toy.name,
                        'item_id':str(toy.id)
                        },
                    })
                    
                    # out of the atomic block everything succeeded perfectly
                    return JsonResponse({
                        'message':'your order confirmed',
                        'razorpay_key_id':settings.RAZORPAY_KEY_ID,
                        'order_id':order['id'],
                        'currency':order['currency'],
                        'amount':order['amount']
                    },status=200)
                
            except Exception as e:
                return JsonResponse({'error':'something went wrong'},status=500)
        return JsonResponse({'error':'method not allowed'},status=405)

                        

client         = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
def signature_check(request):
    if request.method == 'POST':
        try:

            #parse the json body payload send by your frontend
            body_data = json.loads(request.body)

            #extract the payment tokens provided by the razorpay popup widget
            razorpay_order_id = body_data.get('raster_order_id')
            razorpay_payment_id = body_data.get('raster_payment_id')
            razorpay_signature = body_data.get('raster_signature')

            #validation fallback ;ensure no tokens are missing 
            if not all ([razorpay_order_id,razorpay_payment_id,razorpay_signature]):
                return JsonResponse({'status':'failed','error':'missing payment tokens'},status=400)

            #construct the verification payload dictionary matching razorpay's exact expectations
            params_dict = {
                'razorpay_order_id':razorpay_order_id,
                'razorpay_payment_id':razorpay_payment_id,
                'razorpay_signature':razorpay_signature,
            }

            #execute the cryptographic verification check [1]
            #if the signature is forged ,fake or manipulated this method automatically raises an exception [1]
            client.utility.verify_payment_signature(params_dict)

            # PRODUCTION STEP : Your payment is 100% verified genuine here 
            # you can now update your database logs safely.
            # example :
            # order :order.objects.get(razorpay_order_id = razorpay_order_id)
            # order.is_paid = True
            # order.razorpay_payment_id = razorpayment_id
            # order.save() 
            
            return JsonResponse({'status':'success',
                                 'message':'payment signature verified successfuly'},status=200)
        except razorpay.errors.SignatureVerificationerror:
            # triggered if a maliciour users alters tokens or tries to spoof a success purchase [1]
            return JsonResponse({'status':'failed',
                                 'error':'cryptographic signature verification failed.Transaction rejected'},status=400)

        except json.JSONDecodeError:
            return JsonResponse({'status':'failed','error':'invalid json data payload'},status=400)

        except Exception as e:
            # catch all fallback for database  connection issues or general code hiccups
            print(f'Signature check eror {e}')
            return JsonResponse({'status':'failed','error':'An internal processing error occured'},status=500)








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
 
    # 4. Fetch all items for this user to calculate totals
    user_items  = Cart_item.objects.filter(user_cart=request.user)
    total_price = sum(item.get_subtotal() for item in user_items)
    total_count = sum(item.quantity for item in user_items)
    
    # 5. Return JSON data to update your frontend dynamically
    return JsonResponse({
        'success': 'Item added successfully',
        'cart_total_price': float(total_price),
        'cart_total_count': total_count,
        'item_quantity': cart_item.quantity
    })

def user_cart_items(request):
    user_items  = Cart_item.objects.filter(user_cart=request.user)
    total_price = sum(item.get_subtotal() for item in user_items) 
   
    context = {
        'cart_items':user_items,
        'total_price':total_price
    } 
    return render(request,'all_cart.html',context)