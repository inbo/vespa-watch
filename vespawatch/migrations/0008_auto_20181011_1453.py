# Generated by Django 2.1.2 on 2018-10-11 12:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vespawatch', '0007_auto_20181010_1321'),
    ]

    operations = [
        migrations.AddField(
            model_name='species',
            name='vernacular_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='species',
            name='vernacular_name_en',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='species',
            name='vernacular_name_nl',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]