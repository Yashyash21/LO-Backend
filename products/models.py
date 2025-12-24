from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.db.models import JSONField


User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="children"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    brand = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")

    # ⭐ EXISTING FIELDS
    is_trending = models.BooleanField(default=False)
    is_top_deal = models.BooleanField(default=False)
    rating = models.FloatField(default=4.0, blank=True)

    # ⭐ ADD HERE — SIZE TYPE
   
   
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductStock(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    size = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("product", "size")

    def __str__(self):
        return f"{self.product.name} - {self.size} ({self.quantity})"



class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")

    # ⭐ Limit to max 3 images
    def save(self, *args, **kwargs):
        if self.product.images.count() >= 3:
            raise ValueError("A product can have a maximum of 3 images.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.product.name}"


# class Cart(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     size = models.CharField(max_length=20, null=True, blank=True)  # ✅ ADD THIS

#     @property
#     def total_items(self):
#         return sum(item.quantity for item in self.items.all())

#     @property
#     def total_price(self):
#         return sum(item.total_price for item in self.items.all())

#     def __str__(self):
#         return f"Cart for {self.user}"

# ============================================================
# 🛒 CART & CART ITEM MODELS (Supports Guest + User)
# ============================================================




class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="carts",
        null=True,
        blank=True
    )
    cart_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
     if self.user:
        return f"Cart for {self.user.email}"
     return f"Guest Cart ({self.cart_code})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        # ✅ Using float instead of Decimal
        return sum(float(item.quantity) * float(item.product.price) for item in self.items.all())

    def save(self, *args, **kwargs):
        # ✅ Auto-generate a cart code if not provided
        if not self.cart_code:
            self.cart_code = get_random_string(length=10)
        super().save(*args, **kwargs)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    # models.py (inside CartItem)
    size = models.CharField(
    max_length=20,
    null=True,
    blank=True
    )



    class Meta:
        unique_together = ("cart", "product","size")

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    @property
    def total_price(self):
        # ✅ Using float instead of Decimal
        return float(self.quantity) * float(self.product.price)


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.email} → {self.product.name}"




    


from django.db import models
from django.conf import settings


class Payment(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    cart = models.OneToOneField(
        Cart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment"
    )

    razorpay_order_id = models.CharField(max_length=255, unique=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.status} - ₹{self.amount}"


from django.db import models
from django.conf import settings
from products.models import Product
from accounts.models import UserAddress
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserAddress


class Order(models.Model):

    STATUS_CHOICES = (
        ("PLACED", "Order Placed"),
        ("CONFIRMED", "Confirmed"),
        ("SHIPPED", "Shipped"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    address = models.ForeignKey(
        UserAddress,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )

    order_id = models.CharField(max_length=200, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PLACED"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    shipped_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    estimated_delivery_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # ✅ Detect status change
        if self.pk:
            old = Order.objects.get(pk=self.pk)

            if old.status != self.status:
                now = timezone.now()

                if self.status == "SHIPPED":
                    self.shipped_at = now

                elif self.status == "OUT_FOR_DELIVERY":
                    self.out_for_delivery_at = now

                elif self.status == "DELIVERED":
                    self.delivered_at = now

        # ✅ Auto set estimated delivery date (5 days)
        if not self.estimated_delivery_date and self.created_at:
            self.estimated_delivery_date = (
                self.created_at.date() + timedelta(days=5)
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_id

   
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    # ✅ ADD SIZE (IMPORTANT)
    size = models.CharField(max_length=20, null=True, blank=True)

    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ ADD THIS
    
   



    def __str__(self):
        return f"{self.product.name} ({self.size}) × {self.quantity}"
