# Generated by Django 3.2.2 on 2023-05-29 09:47

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tinkoff_payments', '0003_auto_20230529_1110_squashed_0005_alter_tinkoffpaymentdata_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tinkoffpaymentdata',
            name='payment_session_lifetime',
            field=models.DurationField(default=datetime.timedelta(seconds=7200), verbose_name='Payment session lifetime'),
        ),
    ]
