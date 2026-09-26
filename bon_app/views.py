from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
from .forms import UserForm,logged_in
from django.contrib.auth import authenticate,login,logout
import razorpay
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse
from .models import Category,Product,CartItem
from django.db import transaction,models
from django.db.models import F,Sum
import json
import logging
from django.core.paginator import Paginator
import uuid
import time
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
    PRODUCTS_PER_PAGE = 10
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Avoid Paginator.count() on every scroll request. The extra row tells
        # us whether another page exists without a separate COUNT(*) query.
        try:
            page_number = max(int(request.GET.get('page', 1)), 1)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid page number.'}, status=400)

        offset = (page_number - 1) * PRODUCTS_PER_PAGE
        products = list(
            Product.objects.filter(stock__gt=0)
            .order_by('-id')
            .only('image', 'name', 'price')[offset:offset + PRODUCTS_PER_PAGE + 1]
        )

        if len(products) > PRODUCTS_PER_PAGE:
            products = products[:PRODUCTS_PER_PAGE]

        return render(request, 'partials/product_cards.html', {'products': products})

    categories = Category.objects.all()
    all_product = Product.objects.filter(stock__gt=0).order_by('-id').only('image','name','price')
    paginator = Paginator(all_product, PRODUCTS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    products = paginator.get_page(page_number)

    return render(request, 'main.html', {
        'categories': categories,
        'products': products
    })

# payments/views.py
client         = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
client.timeout = 200
logger = logging.getLogger(__name__)

def buy(request, productId):
    if request.method != 'POST':
        return JsonResponse({'Error': 'Method not allowed'}, status=405)

    # Phase 1: Verify and Secure Stock safely
    try:
        with transaction.atomic():
            try:
                toy_to_buy = Product.objects.select_for_update().get(id=productId)
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
        return JsonResponse({'error':'method not allowed'},status=405)
    try:
        data = json.loads(request.body)
        client.utility.verify_payment_signature(data)
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({'error':'signature verification failed'},status=400)
    return JsonResponse({'success':'signature verified successfullt'},status=200)

def category_products_view(request, slug):
    # 1. OPTIMIZATION: Fetch category AND all its related products in ONE database query
    # Note: Use quotes around 'products' (the related_name on your Product model)
    category  = get_object_or_404(
        Category.objects.prefetch_related('products'), 
        slug=slug
    )
    category_list = Category.objects.all()
    
    # 2. Get all products belonging to this specific category
    products = category.products.all()
    
    # 3. Render a single template, passing the dynamic data
    return render(request, 'category.html', {
        'category': category,
        'products': products,
        'category_list':category_list
    })

def log_out(request):
    # print('before logout:',list(request.session.items()))
    logout(request)
    # print('after logout:',list(request.session.items()))
    return redirect('logged')

@login_required
@transaction.atomic  # Ensures database integrity
def add_to_cart(request, productId):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    # 1. Safely find the product
    try:
        toy = Product.objects.select_for_update().get(id=productId)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)

    # 2. Check if product is in stock
    if toy.stock <= 0:
        return JsonResponse({'error': 'out of stock'}, status=400)

    # 3. Get or create the cart item
    cart_item, created = CartItem.objects.get_or_create(
        user_cart=request.user,
        product=toy,
        defaults={'quantity':1 }
    )
    if not created:
        cart_item.quantity = F('quantity') + 1
        cart_item.save(update_fields=['quantity'])
        cart_item.refresh_from_db()
    
    # 5. Deduct exactly ONE from stock 
    toy.stock = F('stock') - 1
    toy.save(update_fields=['stock'])

    return JsonResponse({'success': 'Item added successfully'},status=200)
                                                                    
def user_cart_items(request):
    user_items  = CartItem.objects.filter(user_cart=request.user)
    total_price = sum(item.get_subtotal() for item in user_items)
    category = Category.objects.all()
    context = {
        'cart_items':user_items,
        'total_price':total_price,
        'categories':category
    } 
    return render(request,'all_cart.html',context)

def cart_deduct(request): 
    if request.method != 'DELETE':
        return JsonResponse({'error': 'method not allowed'}, status=405)
        
    try:
        with transaction.atomic():
            # 1. Grab all cart items for the logged-in user
            cart_items = CartItem.objects.filter(user_cart=request.user)
            
            # 2. Check if the cart is already empty cleanly
            if not cart_items.exists():
                return JsonResponse({'error': 'Your cart is already empty'}, status=404)

            # 3. Direct Re-stock loop (No nested loop or Product.objects.all() needed)
            for item in cart_items:
                product = item.product
                product.stock += item.quantity # Add cart quantity back to store stock
                product.save()                 # ✅ Crucial! Save the change to the database
                
            # 4. Wipe the user's entire cart items out at once
            cart_items.delete()
            
            return JsonResponse({'success': True, 'message': 'Cart emptied and items re-stocked successfully.'}, status=200)
            
    except Exception as e:
        print(f"Error emptying cart: {str(e)}") # Keep this for terminal debugging
        return JsonResponse({'error': 'Something went wrong while processing your request.'}, status=500)

# Add this to the top of your views.py file

def user_cart_order_payment(request):
    if not request.method == 'POST':
        return JsonResponse({'error':'method not allowed'},status=405)
        
    user_cart = CartItem.objects.filter(user_cart = request.user)
    if not user_cart.exists():
        return JsonResponse({'error':'user not found'},status=404)
        
    total_price = sum(item.get_subtotal() for item in user_cart)
    round_to_paise = int(total_price * 100) # Ensure amount is an integer
    
    # 1. Comma-separated list is safe here inside the 'notes' field (max 2048 characters total for notes)
    item_names = ", ".join([item.product.name for item in user_cart])

    # 2. FIX: Generate a clean, unique receipt string that stays well under 56 characters
    # Example output: rcpt_1727375185_a1b2c3d4
   
    unique_suffix = uuid.uuid4().hex[:8] # Short 8-character unique string
    receipt_id = f"rcpt_{int(time.time())}_{unique_suffix}" 
   
    # create order using razorpay
    order = client.order.create(data={
        'amount': round_to_paise,
        'currency': 'INR',
        'notes': {
            'email': request.user.email,
            'user': request.user.username,
            'item': item_names # Keeps your item breakdown visible in Razorpay dashboard notes
        },
        'receipt': receipt_id # Now strictly unique and short (approx 20-25 characters)
    })

    # return success order data
    return JsonResponse({
        'key': settings.RAZORPAY_KEY_ID,
        'amount': order['amount'],
        'currency': order['currency'],
        'notes': order['notes'],
        'order_id': order['id'],
        'receipt': order['receipt']
    })

def increment_item(request,id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                cart_item = CartItem.objects.select_for_update().filter(id=id).first() 
                if not cart_item:
                    return JsonResponse({'error':'item dnt exists'},status=404)
                product = Product.objects.select_for_update().filter(id=cart_item.product_id,stock__gt=0).first()
                if not product:
                    return JsonResponse({'error':'out of stock'},status = 403)
              
                cart_item.quantity = F('quantity') + 1
                cart_item.save(update_fields=['quantity'])
                cart_item.refresh_from_db()
                new_quantity = cart_item.quantity
                    
                product.stock = F('stock') - 1
                product.save(update_fields=['stock'])

                total_cart_item = CartItem.objects.filter(user_cart=request.user).aggregate(
                        total_price=Sum(F('quantity') * F('product__price'))
                    )

                user_cart_total_price = total_cart_item['total_price']

                return JsonResponse({'success':True,
                                         'message':'item added succesfully',
                                         'price':user_cart_total_price,
                                         'qty':new_quantity},
                                          status = 200)
            
        except Exception as e:
            return JsonResponse({'error':'something wrong'},status=500)   
    return JsonResponse({'error':'method not allowed'},status=405)


def decrement_item(request, id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)    
    try:
        with transaction.atomic():
            # Lock row because we will read, modify, and update on condition
            item_in_cart = CartItem.objects.select_for_update().filter(id=id, user_cart=request.user).first()

            if not item_in_cart:
                return JsonResponse({'error': 'item not in cart'}, status=404)
            
            # No row locking because we are performing a blind write below
            item_in_product = Product.objects.filter(id=item_in_cart.product.id).first()

            if not item_in_product:
                return JsonResponse({'error': 'item not in product'}, status=404)

            if item_in_cart.quantity > 1:
                item_in_cart.quantity = F('quantity') - 1
                item_in_cart.save(update_fields=['quantity'])
                item_in_cart.refresh_from_db()
                new_quantity = item_in_cart.quantity
            else:
                item_in_cart.delete()
                new_quantity = 0  # Let the execution flow down naturally!
            
            # This runs seamlessly for BOTH paths now
            item_in_product.stock = F('stock') + 1
            item_in_product.save(update_fields=['stock'])

            # Calculate total remaining price
            total_price_agg = CartItem.objects.filter(user_cart=request.user).aggregate(
                total=Sum(F('quantity') * F('product__price'))
            )
            
            return JsonResponse({
                'success': True,
                'qty': new_quantity,
                'price': int(total_price_agg['total'] if total_price_agg['total'] is not None else 0),
                'message': 'Cart updated successfully' # Added message to support your frontend toast!
            }, status=200)
            
    except Exception as e:
        # Temporary tip: return str(e) during testing to see exact errors on screen
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
