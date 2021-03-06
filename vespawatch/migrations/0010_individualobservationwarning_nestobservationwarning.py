# Generated by Django 2.1.5 on 2019-03-15 15:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vespawatch', '0009_add_new_page_fragments'),
    ]

    operations = [
        migrations.CreateModel(
            name='IndividualObservationWarning',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
                ('datetime', models.DateTimeField()),
                ('observation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='warnings', to='vespawatch.Individual')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NestObservationWarning',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
                ('datetime', models.DateTimeField()),
                ('observation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='warnings', to='vespawatch.Nest')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
