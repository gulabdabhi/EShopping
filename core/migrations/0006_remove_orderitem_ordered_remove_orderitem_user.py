# Generated by Django 4.2 on 2023-04-07 19:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_orderitem_ordered_orderitem_quantity_orderitem_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='ordered',
        ),
        migrations.RemoveField(
            model_name='orderitem',
            name='user',
        ),
    ]
