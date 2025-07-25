# Generated by Django 5.2.1 on 2025-07-09 08:58

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('upload', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('price', models.FloatField(default=0)),
                ('quantity', models.IntegerField(default=1)),
                ('description', models.TextField()),
                ('photo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product', to='upload.file')),
            ],
            options={
                'ordering': ['created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.IntegerField(default=1)),
                ('status', models.CharField(blank=True, choices=[('Pending', 'Pending'), ('Cancelled', 'Cancelled'), ('Accepted', 'Accepted')], default='Pending', max_length=10, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders_user', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders_product', to='shop.product')),
            ],
            options={
                'ordering': ['created_at'],
                'abstract': False,
            },
        ),
    ]

