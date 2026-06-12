from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from .forms import UserForm,logged_in
from django.contrib.auth import authenticate,login,logout
import razorpay
from django.conf import settings
from .forms import OrderForm
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse

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
        return render(request, "main.html", {"form": form})

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
        # 'razorpay_key_id':'rzp_test_RR3wUShtuRm0jd',
        'razorpay_key_id':settings.RAZORPAY_KEY_ID,
        'order':order
    }
    return render(request, "payment_interface.html", context)
    # return render(request, "payment_interface.html")

def plushies(request):
    return render(request,"plushies.html")

def kitty(request):
    return render(request,"kitty.html")

def mofusand(request):
    return render(request,"mofusand.html")

def miffy(request):
    return render(request,"miffy.html")

def photo_holder(request):
    return render(request,"photo_holder.html")

def keychain(request):
    return render(request,"keychain.html")

def cinnamonrol(request):
    return render(request,"cinnamonrol.html")
    
def log_out(request):
    # print('before logout:',list(request.session.items()))
    logout(request)
    # print('after logout:',list(request.session.items()))
    return redirect('logged')

def all_cart_items(request,toy_value):
    if request.method == 'POST':    
        print(toy_value)
        return JsonResponse({'success':'cart_added'},status=200)
    return JsonResponse({'error':'method not allwed'},status=405)