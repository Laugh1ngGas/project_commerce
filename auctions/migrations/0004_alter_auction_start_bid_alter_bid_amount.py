# Generated by Django 4.0.4 on 2022-06-24 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0003_alter_auction_categoy_alter_auction_picture_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='start_bid',
            field=models.DecimalField(decimal_places=2, max_digits=15),
        ),
        migrations.AlterField(
            model_name='bid',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=15),
        ),
    ]
