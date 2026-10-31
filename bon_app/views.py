from django.shortcuts import render,redirect,get_object_or_404
from .forms import UserForm,logged_in
from django.contrib.auth import authenticate,login,logout
import razorpay
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse
from .models import Category,Product,CartItem
from django.db import transaction
from django.db.models import F,Sum,When,Case,PositiveBigIntegerField
import json
import logging
from django.core.paginator import Paginator
import uuid
import time

def signup_user(request):
    if request.method == 'POST':
        form  = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit= True)
            login(request,user)
            return redirect('main_page')
        else:
            return render(request,'user_creation.html',{'form':form})
    form = UserForm()
    return render(request,'user_creation.html',{'form':form})

def user_log_in(request):
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST': 
        form = logged_in(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user_access = authenticate(request, username=username, password=password)

            if user_access is not None:
                login(request,user_access)
                # 5. Redirect user
                if next_url and url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                ):
                    return redirect(next_url)
                return redirect('main_page')
            else:
                form.add_error(None, 'Invalid username or Password')
    else:
        form = logged_in()

    return render(request, 'login.html', {'form': form, 'next': next_url})

def main_page(request):
    PRODUCTS_PER_PAGE = 10
    if not request.session.session_key:
        request.session.create()
        request.session.modified = True
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Avoid Paginator.count() on every scroll request. The extra row tells
        # us whether another page exists without a separate COUNT(*) query.
        try:
            page_number = max(int(request.GET.get('page', 1)), 1)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid page number.'}, status=400)

        offset = (page_number - 1) * PRODUCTS_PER_PAGE
        products = list(Product.objects.filter(stock__gt=0).order_by('-id').only('image', 'name', 'price')[offset:offset + PRODUCTS_PER_PAGE + 1])

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


def initiate_razorpay_checkout(request, productId):
    # 1: Ensure user is authenticated before proceeding
    if not request.user.is_authenticated:
        next_url = '/'
        login_url = f"/logged/?next={next_url}"
        # 2: Return a json response with 401 Unauthorized and the login url for the frontend to redirect the user
        return JsonResponse({'authenticated':'false',
                             'next_url':login_url},status = 401)
    # 3: Ensure the request method is Post for checkout initiation
    if request.method != 'POST':
        return JsonResponse({'Error': 'Method not allowed'}, status=405)
    
    # Phase 1: -Verify and Secure Stock safely
    try:
        with transaction.atomic():
            try:
                toy_to_buy = Product.objects.select_for_update().get(id=productId)
            except Product.DoesNotExist:
                return JsonResponse({'Error':'Item not found'}, status=404)

            if toy_to_buy.stock <= 0:
                return JsonResponse({'Error': 'Out of stock'}, status=409)
            
            # Cache values needed for the API call before leaving transaction context
            amount_paise = toy_to_buy.round_to_paise()
            item_name = toy_to_buy.name
            item_id_in_str = str(toy_to_buy.id)

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
                'item_id':item_id_in_str,
            },
            'receipt': f'rcpt_{item_id_in_str}',
        })

    except Exception as api_err:
        # Log the exact Razorpay API failure to your terminal console
        import traceback
        print(traceback.format_exc())
        logger.error(f"Razorpay API failure: {api_err}")
        
        # Phase 3: Rollback stock cleanly if API failed
        try:
            with transaction.atomic():
                # Avoid select_for_update here to prevent deadlocks during failure recovery
                product_rollback = Product.objects.get(id=productId)
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
def cryptographic_signature_check(request):
    if request.method != 'POST':
        return JsonResponse({'error':'method not allowed'},status=405)
    try:
        data = json.loads(request.body)
        client.utility.verify_payment_signature(data)
        product_id = data['notes']['item_id']
        Product.objects.filter(id=product_id).update(stock=F('stock') - 1)
        CartItem.objects.filter(user_cart=request.user,product_id=product_id).delete()
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

def user_log_out(request):
    # print('before logout:',list(request.session.items()))
    logout(request)
    # print('after logout:',list(request.session.items()))
    return redirect('main_page')

  # Ensures database integrity

def add_to_cart(request, productId):
    # Add this line at the start of your views:
    print("CURRENT SESSION ID:", request.session.session_key)

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)
     
    # handle anonymous users by storing cart in session
    if not request.user.is_authenticated:
        product_id = str(productId)
        try:     
            toy = Product.objects.get(id=productId)
        except Product.DoesNotExist:
            return JsonResponse({'error':'Item not found'},status=404)
        
        # 1. check the stock of the product
        if toy.stock <= 0:
            return JsonResponse({'error':'out of stock'},status=400)

        # save item in session cart for anonymous users
        cart = request.session.get('anonymous_cart',{})
        cart[product_id] = cart.get(product_id,0) + 1
        request.session['anonymous_cart'] = cart
        request.session.modified = True
        logger.info(f"Anonymous user added product {product_id} to session cart.\nCurrent cart contains: {cart}")
        return JsonResponse({'success':'Item added'},status = 200)

    # 1. Safely find the product
    try:
        with transaction.atomic():
            try:
                toy = Product.objects.select_for_update().get(id=productId)
            except Product.DoesNotExist:
                return JsonResponse({'error':'Item not found'},status=404)
            # 2. Check if product is in stock using the pre-fetched related object
            # (Assuming your Stock model has a field called 'quantity')
            if toy.stock <= 0:
                return JsonResponse({'error': 'out of stock'}, status=400)

            # 3. Get or create the cart item (passing the single 'toy' instance)
            cart_item, created = CartItem.objects.get_or_create(
                user_cart=request.user,
                product=toy,
                defaults={'quantity': 1}
            )
            
            # 4. If it already exists, increment the quantity safely
            if not created:
                cart_item.quantity = F('quantity') + 1
                cart_item.save(update_fields=['quantity'])
          
            # Use the exact field name in your Stock model
            Product.objects.filter(id=toy.id).update(stock=F('stock')-1)    
        return JsonResponse({'success': 'Item added successfully'}, status=200)
       
    except Exception as e:
        logger.error(f"Error adding product {productId} to cart for user {request.user.id} : {str(e)}")
        return JsonResponse({'error': 'An error occurred during transaction processing.'}, status=500)

from django.core.cache import cache                                        
def show_user_cart_items(request):
    # Add this line at the start of your views:
    print("CURRENT SESSION ID:", request.session.session_key)

    # cache the category for dropdown menu
    category = cache.get('all_categories')
    if not category:
        category = list(Category.objects.all())
        cache.set('all_categories',category,60*60)

    # check if user not authenticated to Show anonymous user cart
    if not request.user.is_authenticated:
        user_cart = request.session.get('anonymous_cart',{})
        if not user_cart:
            context = {'cart_items':[],'total_price':0,'categories':category}
            return render(request,'all_cart.html')

        product_ids = list(user_cart.keys())
        products = Product.objects.filter(id__in=product_ids).in_bulk()

        user_items = []
        total_price = 0
        
        for prodid , prod_quan in user_cart.items():            
            product = products.get(int(prodid))
            if product:
                subtotal = product.price * prod_quan
                total_price += subtotal
                user_items.append({
                    'product':product,
                        'id':int(prodid),
                        'quantity':prod_quan,
                        'total_price':subtotal})
                
        context = {
                    'cart_items':user_items,
                    'total_price':total_price,
                    'categories':category
                }       
    else:        
        user_items  = CartItem.objects.filter(user_cart=request.user).select_related('product','product__category')
        total_price = sum(item.product.price * item.quantity for item in user_items)
        context = {
                'cart_items':user_items,
                'total_price':total_price,
                'categories':category
            } 
    return render(request,'all_cart.html',context)

def wipe_user_cart(request): 
    if request.method != 'DELETE':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    
    # Delete anonymous session cart data  
    if not request.user.is_authenticated:
        user_session = request.session.get('anonymous_cart',{})
        if user_session:
            # use flush to delete session data both from browser cookies and django session table
            request.session.flush()
            logger.info(f"session deleted")
            return JsonResponse({'success':'cart deleted'},status = 200)
        else:
            return JsonResponse({'error':'session not found'},status = 404)
    try:
        with transaction.atomic():
            # 1. Grab all cart items for the logged-in user
            cart_items = list(CartItem.objects.filter(user_cart=request.user))
             
            # 2. Check if the cart is already empty cleanly
            if not cart_items:
                return JsonResponse({'error': 'Your cart is already empty'}, status=404)
            
            cases = [When(id=i.product_id , then=F('stock') + i.quantity) for i in cart_items]
            Product.objects.filter(id__in=[i.product_id for i in cart_items]).update(stock = Case(*cases , default=F('stock'),output_field=PositiveBigIntegerField()))

            # 4. Wipe the user's entire cart items out at once
            CartItem.objects.filter(user_cart=request.user).delete()
            return JsonResponse({'success': True, 'message': 'Cart emptied and items re-stocked successfully.'}, status=200)
            
    except Exception as e:
        print(f"Error emptying cart: {str(e)}") # Keep this for terminal debugging
        return JsonResponse({'error': 'Something went wrong while processing your request.'}, status=500)

# Add this to the top of your views.py file

def user_cart_order_payment(request):
    if not request.method == 'POST':
        return JsonResponse({'error':'method not allowed'},status=405)
    if not request.user.is_authenticated:
        next_url = '/show_user_cart_items/'
        login_url = f'/logged/?next={next_url}'
        return JsonResponse({'error':'please login to order','authenticated':'false','next_url':login_url},status=401)
        
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

def increment_item(request,productId):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # query both the cartItem and its related product at one trip
                cart_item = CartItem.objects.filter(id=productId,user_cart=request.user).select_related('product').select_for_update().first() 
                
                if not cart_item:
                    return JsonResponse({'error':'item dnt exists'},status=404)
                
                if cart_item.product.stock < 1:
                    return JsonResponse({'error':'out of stock'},status = 403)

                #update in the db level
                CartItem.objects.filter(id=cart_item.id).update(quantity=F('quantity') + 1)    
                Product.objects.filter(id=cart_item.product_id).update(stock=F('stock') - 1)
                
                #update the quantity object
                new_quantity = cart_item.quantity + 1
                
                total_cart_item = CartItem.objects.filter(user_cart=request.user).aggregate(
                        total_price=Sum(F('quantity') * F('product__price'))
                    )['total_price'] or 0

                return JsonResponse({'success':True,
                                         'message':'item added succesfully',
                                         'price':int(total_cart_item),
                                         'qty':new_quantity},
                                          status = 200)
            
        except Exception as e:
            # Temporary tip: return str(e) during testing to see exact errors on screen
            import traceback
            print(traceback.format_exc()) 
            return JsonResponse({'error':'something wrong'},status=500)   
    return JsonResponse({'error':'method not allowed'},status=405)


def decrement_item(request, productId):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)    
    try:
        with transaction.atomic():
            # Lock row because we will read, modify, and update on condition
            item_in_cart = CartItem.objects.filter(id=productId, user_cart=request.user).select_related('product').select_for_update().first()

            if not item_in_cart:
                return JsonResponse({'error': 'item not in cart'}, status=404)
            
            if item_in_cart.quantity > 1:
                CartItem.objects.filter(id=item_in_cart.id).update(quantity=F('quantity') - 1)
                Product.objects.filter(id=item_in_cart.product_id).update(stock=F('stock') + 1)

                # update the python object so aggregate function can see the updated value
                new_quantity  = item_in_cart.quantity - 1
                 
            else:
                Product.objects.filter(id=item_in_cart.product_id).update(stock=F('stock') + 1)
                item_in_cart.delete()
                new_quantity = 0  # Let the execution flow down naturally! 

            # Calculate total remaining price
            total_price_agg = CartItem.objects.filter(user_cart=request.user).aggregate(
                total=Sum(F('quantity') * F('product__price'))
            )['total'] or 0

            return JsonResponse({
                'success': True,
                'qty': new_quantity,
                'price': int(total_price_agg),
                'message': 'Cart updated successfully' # Added message to support your frontend toast!
            }, status=200)
            
    except Exception as e:
        # Temporary tip: return str(e) during testing to see exact errors on screen
        import traceback
        print(traceback.format_exc()) 
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)