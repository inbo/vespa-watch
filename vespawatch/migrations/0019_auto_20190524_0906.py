# Generated by Django 2.2.1 on 2019-05-24 07:06

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('vespawatch', '0018_auto_20190522_1200'),
    ]

    operations = [
        migrations.AddField(
            model_name='individual',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='nest',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
