# Generated by Django 3.2.2 on 2023-05-05 08:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('rent', '0022_auto_20230505_1515'),
    ]

    operations = [
        migrations.CreateModel(
            name='TinkoffPaymentData',
            fields=[
                ('payment_id', models.CharField(max_length=23, primary_key=True, serialize=False, verbose_name='Payment ID')),
                ('payment_strategy', models.CharField(choices=[('card', 'CARD'), ('sbp', 'SBP')], max_length=4, verbose_name='Payment strategy')),
                ('payload_type', models.CharField(choices=[('payment_url', 'PAYMENT_URL'), ('qr_url', 'QR_URL'), ('qr_image', 'QR_IMAGE')], max_length=11, verbose_name='Payment payload type')),
                ('payload', models.TextField(verbose_name='Payment payload')),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='payment_data', related_query_name='payment_data', to='rent.order', verbose_name='Order')),
            ],
            options={
                'verbose_name': 'Tinkoff payment data',
                'verbose_name_plural': 'Tinkoff payments data',
            },
        ),
    ]
