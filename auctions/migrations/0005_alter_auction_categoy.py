# Generated by Django 4.0.4 on 2022-06-24 14:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0004_alter_auction_start_bid_alter_bid_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='categoy',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='category', to='auctions.category'),
        ),
    ]