# Generated by Django 4.2 on 2023-04-09 17:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_order_billing_address_order_payment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='stripe_charge_id',
        ),
    ]