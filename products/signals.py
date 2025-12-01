# signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Cart, CartItem


@receiver(user_logged_in)
def merge_guest_cart_to_user(sender, user, request, **kwargs):
    """
    Merge guest cart (if exists) into user's cart after login.
    """
    session_id = request.session.get("cart_session_id")
    if not session_id:
        return

    try:
        guest_cart = Cart.objects.get(session_id=session_id, user=None)
    except Cart.DoesNotExist:
        return

    # Get or create user's cart
    user_cart, _ = Cart.objects.get_or_create(user=user)

    # Move items from guest cart → user cart
    for item in guest_cart.items.all():
        cart_item, created = CartItem.objects.get_or_create(
            cart=user_cart, product=item.product
        )
        if not created:
            cart_item.quantity += item.quantity
        else:
            cart_item.quantity = item.quantity
        cart_item.save()

    # Delete guest cart after merge
    guest_cart.delete()
    request.session.pop("cart_session_id", None)


