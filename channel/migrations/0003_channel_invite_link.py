# Generated by Django 5.2.1 on 2025-07-07 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('channel', '0002_channel_chat_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='invite_link',
            field=models.URLField(default=1),
            preserve_default=False,
        ),
    ]
