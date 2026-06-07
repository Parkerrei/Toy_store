class Session_Cart:
    def __init__(self,request):
        self.session = request.session
        cart = self.session.get('cart_session_id')
        if not cart:
            cart = self.session['cart_session_id']={}
        self.cart = cart
        
    def add(self,product_id,quantity=1):
        product_id = str(product_id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity':0}
        self.cart[product_id]['quantity'] +=quantity
        self.session.modified = True