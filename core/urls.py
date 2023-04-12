from django.urls import path
from .views import (
                    HomeView, 
                    ItemDetailView, 
                    OrderSummaryView,
                    CheckoutView,
                    PaymentView,
                    AddCouponView,
                    add_to_cart, 
                    remove_from_cart, 
                    remove_items_from_cart
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('product/<slug>', ItemDetailView.as_view(), name='product'),
    path('order-summary', OrderSummaryView.as_view(), name='order-summary'),
    path('checkout', CheckoutView.as_view(), name='checkout'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('add-to-cart/<slug>', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>/', remove_items_from_cart,
         name='remove-item-from-cart'),
]
