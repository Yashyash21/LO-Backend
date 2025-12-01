from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils.crypto import get_random_string
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import razorpay
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from products.models import Cart
from .models import Payment
from .serializers import PaymentSerializer



from .models import (
    Category, Product, Wishlist
)
from .serializers import (
    CategorySerializer, ProductSerializer,
    CartSerializer, CartItemSerializer,
    WishlistSerializer
)
from .models import Cart, CartItem

def merge_guest_cart(user, cart_code):
    try:
        guest_cart = Cart.objects.filter(cart_code=cart_code, paid=False).first()
        if not guest_cart:
            return
        
        user_cart, _ = Cart.objects.get_or_create(user=user, paid=False)

        for item in guest_cart.items.all():
            # Merge item
            existing, created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=item.product,
                size=item.size,
                defaults={"quantity": item.quantity}
            )
            if not created:
                existing.quantity += item.quantity
                existing.save()

        guest_cart.delete()

    except Exception as e:
        print("Cart merge error:", e)

# ============================================================
# 🏷 CATEGORY & PRODUCT APIs
# ============================================================

@api_view(['GET'])
def category_list(request, path=None):
    categories = Category.objects.none()
    if not path:
        categories = Category.objects.filter(parent=None)
    else:
        slugs = path.strip("/").split("/")
        parent = None
        category = None
        for slug in slugs:
            category = get_object_or_404(Category, slug=slug, parent=parent)
            parent = category
        if category:
            categories = category.children.all()

    serializer = CategorySerializer(categories, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def products_by_category(request, path):
    slugs = path.strip("/").split("/")
    parent = None
    category = None
    for slug in slugs:
        category = get_object_or_404(Category, slug=slug, parent=parent)
        parent = category

    def get_all_subs(cat):
        subs = cat.children.all()
        result = list(subs)
        for sub in subs:
            result += get_all_subs(sub)
        return result

    subcats = get_all_subs(category)
    categories_to_search = [category] + subcats
    products = Product.objects.filter(category__in=categories_to_search).distinct()
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    serializer = ProductSerializer(product, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def search_products(request):
    queryset = Product.objects.all()

    # 🔍 Main search (name + desc + brand + category)
    query = request.GET.get('q') or request.GET.get('search')
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query)
        )

    # 💰 Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price and max_price:
        queryset = queryset.filter(price__gte=min_price, price__lte=max_price)

    # 🏷 Brand filter (partial match)
    brand = request.GET.get('brand')
    if brand:
        queryset = queryset.filter(brand__icontains=brand)

    # 📂 Category filter (slug)
    category = request.GET.get('category')
    if category:
        queryset = queryset.filter(category__slug=category)

    # 🔁 Remove duplicates
    queryset = queryset.distinct()

    serializer = ProductSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


# ============================================================
# 🛒 CART SYSTEM (Auto Cart Creation)
# ============================================================

@api_view(["POST"])
def add_item(request):
    """
    Add a product to cart.
    Automatically generates a cart_code if not provided.
    Works for guest and logged-in users.
    """
    try:
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        cart_code = request.data.get("cart_code")

        if not product_id:
            return Response({"error": "Product ID is required"}, status=400)

        # ✅ Auto-generate a cart_code if not provided
        if not cart_code:
            cart_code = get_random_string(length=10)

        # ✅ Get or create cart (user or guest)
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user, paid=False)
        else:
            cart, _ = Cart.objects.get_or_create(cart_code=cart_code, paid=False)

        # ✅ Get product
        product = get_object_or_404(Product, id=product_id)

        # ✅ Add or update cart item
        size = request.data.get("size")  # 👈 READ SIZE FROM API

        cartitem, created = CartItem.objects.get_or_create(
         cart=cart,
         product=product,
         size=size  # 👈 IMPORTANT
          )
        if created:
            cartitem.quantity = quantity
        else:
            cartitem.quantity += quantity
        cartitem.save()

        serializer = CartItemSerializer(cartitem, context={"request": request})
        return Response({
            "message": "Item added to cart successfully ✅",
            "cart_code": cart.cart_code,
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


# ------------------------
# 🧾 Check if product is in cart
# ------------------------
@api_view(['GET'])
def product_in_cart(request):
    cart_code = request.query_params.get("cart_code")
    product_id = request.query_params.get("product_id")

    if not cart_code or not product_id:
        return Response({"error": "cart_code and product_id are required"}, status=400)

    cart = get_object_or_404(Cart, cart_code=cart_code)
    product = get_object_or_404(Product, id=product_id)
    exists = CartItem.objects.filter(cart=cart, product=product).exists()

    return Response({'product_in_cart': exists})


# ------------------------
# 📊 Cart Summary
# ------------------------
@api_view(['GET'])
def get_cart_stat(request):
    cart_code = request.query_params.get("cart_code")
    cart = get_object_or_404(Cart, cart_code=cart_code)
    serializer = CartSerializer(cart)
    return Response(serializer.data)


# ------------------------
# 🛍️ Get Full Cart
# ------------------------
@api_view(['GET'])
def get_cart(request):
    """
    Always returns a valid cart (auto-creates one if missing).
    Works for both guests (cart_code) and logged-in users.
    """
    user = request.user if request.user.is_authenticated else None

    # ✅ For logged-in users
    if user:
        cart, created = Cart.objects.get_or_create(user=user, paid=False)

    else:
        # ✅ For guest users
        cart_code = request.query_params.get("cart_code") or request.COOKIES.get("cart_code")

        if not cart_code:
            # generate a random cart_code
            cart_code = get_random_string(length=10)
            cart = Cart.objects.create(cart_code=cart_code)
        else:
            cart, created = Cart.objects.get_or_create(cart_code=cart_code, paid=False)

    serializer = CartSerializer(cart, context={'request': request})
    response = Response(serializer.data)

    # ✅ Save cart_code for guest in cookies (optional)
    if not user:
        response.set_cookie("cart_code", cart.cart_code, max_age=7*24*3600)  # 1 week

    return response



# ------------------------
# ✏️ Update Quantity
# ------------------------
@api_view(['PATCH'])
def update_quantity(request):
    try:
        item_id = request.data.get("item_id")
        quantity = int(request.data.get("quantity", 1))
        cartitem = get_object_or_404(CartItem, id=item_id)

        if quantity <= 0:
            cartitem.delete()
            return Response({"message": "Item removed"}, status=204)

        cartitem.quantity = quantity
        cartitem.save()
        serializer = CartItemSerializer(cartitem, context={"request": request})
        return Response({"data": serializer.data, "message": "Quantity updated"}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


# ------------------------
# ❌ Delete Cart Item
# ------------------------
@api_view(['POST'])
def delete_cartitem(request):
    item_id = request.data.get("item_id")
    cartitem = get_object_or_404(CartItem, id=item_id)
    cartitem.delete()
    return Response({"message": "Item deleted successfully"}, status=204)


# ============================================================
# ❤️ WISHLIST APIs
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_wishlist(request):
    wishlist = Wishlist.objects.filter(user=request.user)
    serializer = WishlistSerializer(wishlist, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_wishlist(request):
    product_id = request.data.get("product_id")
    product = get_object_or_404(Product, id=product_id)

    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        return Response({"detail": "Already in wishlist."}, status=status.HTTP_200_OK)

    serializer = WishlistSerializer(wishlist_item, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request, product_id):
    wishlist_item = get_object_or_404(Wishlist, user=request.user, product_id=product_id)
    wishlist_item.delete()
    return Response({"detail": "Removed from wishlist."}, status=status.HTTP_204_NO_CONTENT)


# ============================================================
# 🔥 TRENDING & TOP DEALS APIs
# ============================================================

@api_view(['GET'])
def trending_products(request):
    items = Product.objects.filter(is_trending=True)
    serializer = ProductSerializer(items, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def top_deals_products(request):
    items = Product.objects.filter(is_top_deal=True)
    serializer = ProductSerializer(items, many=True, context={'request': request})
    return Response(serializer.data)




# ?????????????????????????????????????


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    try:
        user = request.user
        cart = Cart.objects.filter(user=user, paid=False).first()

        if not cart or not cart.items.exists():
            return Response({"error": "Your cart is empty."}, status=400)

        amount = int(cart.total_price * 100)
        currency = "INR"

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # 1️⃣ Create Razorpay Order
        razorpay_order = client.order.create(dict(amount=amount, currency=currency, payment_capture="1"))

        # 2️⃣ IMPORTANT FIX — Avoid Duplicate Payment
        payment, created = Payment.objects.get_or_create(
            user=user,
            cart=cart,
            defaults={
                "amount": cart.total_price,
                "currency": currency,
                "razorpay_order_id": razorpay_order["id"],
                "status": "created",
            }
        )

        # If payment already exists → update order_id & amount
        if not created:
            payment.amount = cart.total_price
            payment.currency = currency
            payment.razorpay_order_id = razorpay_order["id"]
            payment.status = "created"
            payment.save()

        serializer = PaymentSerializer(payment)

        return Response({
            "key": settings.RAZORPAY_KEY_ID,
            "amount": amount,
            "currency": currency,
            "order_id": razorpay_order["id"],
            "user_email": user.email,
            "user_phone": user.phone,
            "payment": serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    try:
        data = request.data

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        # -------------------------------
        # 1️⃣ VERIFY RAZORPAY SIGNATURE
        # -------------------------------
        params_dict = {
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"],
        }

        client.utility.verify_payment_signature(params_dict)

        # -------------------------------
        # 2️⃣ FETCH PAYMENT OBJECT
        # -------------------------------
        payment = Payment.objects.filter(
            razorpay_order_id=data["razorpay_order_id"]
        ).first()

        if not payment:
            return Response({"error": "Payment not found"}, status=404)

        # Update payment info
        payment.razorpay_payment_id = data["razorpay_payment_id"]
        payment.razorpay_signature = data["razorpay_signature"]
        payment.status = "success"
        payment.save()

        # -------------------------------
        # 3️⃣ CREATE ORDER
        # -------------------------------
        from products.models import Order, OrderItem   # ✅ FIXED IMPORT
        import uuid

        cart = payment.cart

        order = Order.objects.create(
            user=request.user,
            order_id=str(uuid.uuid4()),
            total_amount=cart.total_price,
            status="Pending"
        )

        # Create each item
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )

        # -------------------------------
        # 4️⃣ CLEAR CART
        # -------------------------------
        cart.items.all().delete()
        cart.paid = True
        cart.save()

        return Response({"message": "Payment verified successfully"}, status=200)

    except razorpay.errors.SignatureVerificationError:
        return Response({"error": "Invalid signature"}, status=400)

    except Exception as e:
        return Response({"error": str(e)}, status=500)




from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)
