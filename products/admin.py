from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Product, Category, Cart, CartItem, Wishlist,ProductImage
from import_export import resources, fields
from import_export.widgets import JSONWidget


# ================================
# 🏷 CATEGORY ADMIN
# ================================
@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    list_display = ('name', 'parent', 'image')
    search_fields = ('name',)


# ================================
# 🛍 PRODUCT ADMIN
# ================================

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 3 


class ProductResource(resources.ModelResource):
    stock = fields.Field(
        column_name="stock",
        attribute="stock",
        widget=JSONWidget()
    )

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "price",
            "original_price",
            "brand",
            "stock",
            "category",
            "is_trending",
            "is_top_deal",
            "rating",
        )

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource   # <-- Add this line

    list_display = (
        'name', 'category', 'price', 'original_price', 'stock',
        'is_trending', 'is_top_deal', 'rating'
    )

    list_filter = ('category','is_trending', 'is_top_deal','rating')
    search_fields = ('name', 'category__name')
    list_editable = ('rating',)    
    inlines = [ProductImageInline]





# ================================
# 🛒 CART ADMIN
# ================================
@admin.register(Cart)
class CartAdmin(ImportExportModelAdmin):
    list_display = ('get_user_email', 'cart_code', 'total_items', 'total_price', 'paid', 'created_at',  'updated_at')
    search_fields = ('user__email', 'cart_code')
    list_filter = ('paid', 'created_at')

    # ✅ Custom method to show user's email (or Guest)
    def get_user_email(self, obj):
        return obj.user.email if obj.user else "Guest Cart"
    get_user_email.short_description = "User Email"


# ================================
# 🧾 CART ITEM ADMIN
# ================================
@admin.register(CartItem)
class CartItemAdmin(ImportExportModelAdmin):
    list_display = ('cart', 'product', 'size', 'quantity', 'total_price', 'added_at')
    list_filter = ('product', 'cart')
    search_fields = ('product__name', 'cart__user__email')


# ================================
# ❤️ WISHLIST ADMIN
# ================================
@admin.register(Wishlist)
class WishlistAdmin(ImportExportModelAdmin):
    list_display = ("user", "product", "added_at")
    search_fields = ("user__email", "product__name")
    list_filter = ("added_at",)








from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    list_display = ("user", "amount", "currency", "status", "razorpay_order_id", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("razorpay_order_id", "user__email")
    ordering = ("-created_at",)


from django.contrib import admin
from .models import Order, OrderItem

admin.site.register(Order)
admin.site.register(OrderItem)
