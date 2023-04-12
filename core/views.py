import random
import string

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View

from .models import Item, OrderItem, Order, BillingAddress, Payment, Coupon
from .forms import CheckoutForm, CouponForm

class HomeView(ListView):
    model = Item
    paginate_by = 8
    template_name = "home.html"

class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not hava any active order")
            return redirect('/')

class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                address = form.cleaned_data.get('address')
                address_2 = form.cleaned_data.get('address_2')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                billing_address = BillingAddress(
                    user=self.request.user,
                    address=address,
                    address_2=address_2,
                    zip=zip,
                    country=country
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'D':
                    return redirect('core:payment', payment_option='debit card')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('core:checkout')
                
            messages.warning(self.request, 'Checkout failed')
            return redirect("core:checkout")

        except ObjectDoesNotExist:
            messages.error(self.request, "You do not hava any active order")
            return redirect("core:order-summary")

class PaymentView(View):  
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False
            }
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("core:checkout")
    
    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)

        # create the payment
        payment = Payment()
        payment.user = self.request.user
        payment.amount = order.get_total()
        payment.save()

        # assign the payment to order

        order_items = order.items.all()
        order_items.update(ordered = True)
        for item in order_items:
            item.save()

        order.ordered = True
        order.payment = payment
        order.save()

        messages.success(self.request, 'Your order was successful')
        return redirect('/')


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered = False
    )
    order_qs = Order.objects.filter(user=request.user, ordered = False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity +=1
            order_item.save()
            messages.info(request, 'This item quantity was updated.')
        else:
            order.items.add(order_item)
            messages.info(request, 'This item was added to your cart.')
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user = request.user, 
            ordered_date = ordered_date
            )
        order.items.add(order_item)
        messages.info(request, 'This item was added to your cart.')
    return redirect("core:order-summary")

@login_required       
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, 'This item was removed your cart.')
            return redirect("core:order-summary")
        else:
            order.delete()
            messages.info(request, 'This item was not in your cart.')
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, 'You do not have any active order')
        return redirect("core:product", slug=slug)

@login_required   
def remove_items_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)

            messages.info(request, 'This item quantity was updated.')
            return redirect("core:order-summary")
        else:
            messages.info(request, 'This item was not in your cart.')
            return redirect("core:order-summary")

    else:
        messages.info(request, 'You do not have any active order')
        return redirect("core:order-summary")
    
def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")