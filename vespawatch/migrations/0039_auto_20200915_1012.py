# Generated by Django 2.2.13 on 2020-09-15 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vespawatch', '0038_auto_20200915_1000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='managementaction',
            name='outcome',
            field=models.CharField(choices=[('PP', 'Professional permas - D treatment'), ('PC', 'Classic permas - D treatment'), ('FD', 'Complete manual removal'), ('PD', 'Partial manual removal'), ('ND', 'Not treated'), ('UK', 'Unknown')], max_length=2, verbose_name='Outcome'),
        ),
    ]
