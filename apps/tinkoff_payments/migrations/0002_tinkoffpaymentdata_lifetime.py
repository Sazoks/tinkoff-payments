# Generated by Django 3.2.2 on 2023-05-25 12:24

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tinkoff_payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tinkoffpaymentdata',
            name='lifetime',
            field=models.DurationField(default=datetime.timedelta(days=1), verbose_name='Lifetime'),
        ),
    ]
