from rest_framework import serializers
from .models import Category, Product, Cart, CartItem, Wishlist, ProductImage, Order, OrderItem, Payment


# ============================================================
# CATEGORY SERIALIZER
# ============================================================
class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "image"]

    def get_image(self, obj):
        request = self.context.get("request")
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None


# ============================================================
# PRODUCT IMAGES
# ============================================================
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["image"]


# ============================================================
# PRODUCT SERIALIZER
# ============================================================
class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    final_price = serializers.SerializerMethodField()
    discount_percent = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()  # 👈 ADD THIS


    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description",
            "price", "original_price",
            "final_price", "discount_percent",
            "brand", "stock", "image", "category",
            "is_trending", "is_top_deal", "images",
           
        ]

    def get_image(self, obj):
        request = self.context.get("request")
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_final_price(self, obj):
        return float(obj.price)

    def get_discount_percent(self, obj):
        if obj.original_price and obj.original_price > obj.price:
            discount = ((obj.original_price - obj.price) / obj.original_price) * 100
            return round(discount)
        return 0


# ============================================================
# CART ITEM SERIALIZER
# ============================================================
class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "total_price", "size"]

    def get_product(self, obj):
        return ProductSerializer(obj.product, context=self.context).data

    def get_total_price(self, obj):
        return round(float(obj.product.price) * float(obj.quantity), 2)


# ============================================================
# MAIN CART SERIALIZER
# ============================================================
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id", "cart_code", "paid",
            "items", "total_items", "total_price",
            "created_at", "updated_at",
        ]

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total_price(self, obj):
        total = sum(item.product.price * item.quantity for item in obj.items.all())
        return round(total, 2)


# ============================================================
# WISHLIST SERIALIZER
# ============================================================
class WishlistSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = ["id", "product", "added_at"]

    def get_product(self, obj):
        return ProductSerializer(obj.product, context=self.context).data


# ============================================================
# ORDER ITEM SERIALIZER
# ============================================================
class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity"]

    def get_product(self, obj):
        return ProductSerializer(obj.product, context=self.context).data


# ============================================================
# ORDER SERIALIZER
# ============================================================
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "order_id", "total_amount", "status", "created_at", "items"]


# ============================================================
# PAYMENT SERIALIZER
# ============================================================
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ("status", "created_at", "updated_at")
