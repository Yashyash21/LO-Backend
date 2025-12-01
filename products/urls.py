from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    # 🏷 Category & Product
    category_list,
    products_by_category,
    product_detail,
    search_products,

    # 🛒 Cart System
    get_cart,
    add_item,
    update_quantity,
    delete_cartitem,
    product_in_cart,
    get_cart_stat,

    # ❤️ Wishlist
    get_wishlist,
    add_to_wishlist,
    remove_from_wishlist,

    # 🔥 Trending & Deals
    trending_products,
    top_deals_products,


    create_order,
    verify_payment,
    get_user_orders

)

urlpatterns = [
    # =====================================================
    # 🏷 CATEGORY & PRODUCT ROUTES
    # =====================================================
    re_path(r"^categories(?:/(?P<path>.+))?/$", category_list, name="category-list"),
    re_path(r"^products/(?P<path>.+)/$", products_by_category, name="products-by-category"),
    path("product/<slug:slug>/", product_detail, name="product-detail"),
    path("search/", search_products, name="search-products"),

    # =====================================================
    # 🛒 CART ROUTES
    # =====================================================
    path("cart/", get_cart, name="get-cart"),
    path("cart/add/", add_item, name="add-to-cart"),
    path("cart/update/", update_quantity, name="update-quantity"),
    path("cart/delete/", delete_cartitem, name="delete-cartitem"),
    path("cart/status/", get_cart_stat, name="get-cart-stat"),
    path("cart/check/", product_in_cart, name="product-in-cart"),

    # =====================================================
    # ❤️ WISHLIST ROUTES
    # =====================================================
    path("wishlist/", get_wishlist, name="get-wishlist"),
    path("wishlist/add/", add_to_wishlist, name="add-to-wishlist"),
    path("wishlist/remove/<int:product_id>/", remove_from_wishlist, name="remove-from-wishlist"),

    # =====================================================
    # 🔥 TRENDING & DEALS ROUTES
    # =====================================================
      path('trending-products/', trending_products),
    path('top-deals/', top_deals_products),


    # ==========================================================
                    #   Payment
    # ==========================================================
    path('create-order/', create_order, name='create-order'),
    path('verify-payment/', verify_payment, name='verify-payment'),
    path("orders/", get_user_orders),

]

# =====================================================
# 📁 MEDIA FILES (Only in DEBUG mode)
# =====================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
