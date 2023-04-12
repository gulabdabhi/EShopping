from statistics import mode
from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django_countries.fields import CountryField
from numpy import true_divide

CATEGORY_CHOICES = (
    ('S', 'Shirts'),
    ('SW', 'Sports wear'),
    ('OW', 'Outwear')
)

LABLE_CHOICES = (
    ('Y', 'primary'),
    ('W', 'secondary'),
    ('D', 'danger')
)

class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    lable = models.CharField(choices=LABLE_CHOICES, max_length=1)
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField()
    
    def __str__(self):
        return self.title
    
    def new_price(self):
        if self.discount_price:
            self.price = self.price - self.discount_price
        else:
            self.price = self.price
        return self.price

    
    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })
    
    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        })
    
    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={
            'slug': self.slug
        })

class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"
    
    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_item_price() - self.get_total_discount_item_price()
        return self.get_total_item_price()

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True, null= True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey(
        'BillingAddress', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.user.username 
    
    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total
    
class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    address = models.CharField(max_length=100)
    address_2 = models.CharField(max_length=100)
    zip = models.CharField(max_length=10)
    country = CountryField(multiple=True)

    def __str__(self):
        return self.user.username

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    
class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code