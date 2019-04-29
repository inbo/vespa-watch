# Generated by Django 2.1.5 on 2019-04-29 09:15

from django.db import migrations, models
import markdownx.models
import vespawatch.models


class Migration(migrations.Migration):

    dependencies = [
        ('vespawatch', '0010_auto_20190318_1408'),
    ]

    operations = [
        migrations.AlterField(
            model_name='identificationcard',
            name='description',
            field=markdownx.models.MarkdownxField(blank=True, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='identificationcard',
            name='description_en',
            field=markdownx.models.MarkdownxField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='identificationcard',
            name='description_nl',
            field=markdownx.models.MarkdownxField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='identificationcard',
            name='identification_picture',
            field=models.ImageField(blank=True, null=True, upload_to=vespawatch.models.IdentificationCard.get_file_path, verbose_name='Photo for identification'),
        ),
        migrations.AlterField(
            model_name='identificationcard',
            name='order',
            field=models.IntegerField(unique=True, verbose_name='Order'),
        ),
        migrations.AlterField(
            model_name='individual',
            name='address',
            field=models.CharField(blank=True, max_length=255, verbose_name='Address'),
        ),
        migrations.AlterField(
            model_name='individual',
            name='behaviour',
            field=models.CharField(blank=True, choices=[('FO', 'Fouraging'), ('HU', 'Hunting at hive'), ('FL', 'At flower'), ('OT', 'Other')], max_length=2, null=True, verbose_name='Behaviour'),
        ),
        migrations.AlterField(
            model_name='individual',
            name='comments',
            field=models.TextField(blank=True, verbose_name='Comments'),
        ),
        migrations.AlterField(
            model_name='individual',
            name='inaturalist_id',
            field=models.BigIntegerField(blank=True, null=True, verbose_name='iNaturalist ID'),
        ),
        migrations.AlterField(
            model_name='individual',
            name='inaturalist_species',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='iNaturalist species'),
        ),
        migrations.AlterField(
            model_name='individual',
            name='individual_count',
            field=models.IntegerField(blank=True, null=True, verbose_name='Individual count'),
        ),
        migrations.AlterField(
            model_name='individual',
            name='latitude',
            field=models.FloatField(verbose_name='Latitude'),
        ),
        migrations.AlterField(
            model_name='individual',
            name='longitude',
            field=models.FloatField(verbose_name='Longitude'),
        ),
        migrations.AlterField(
            model_name='individualpicture',
            name='image',
            field=models.ImageField(upload_to=vespawatch.models.IndividualPicture.get_file_path, verbose_name='Photo'),
        ),
        migrations.AlterField(
            model_name='managementaction',
            name='action_time',
            field=models.DateTimeField(verbose_name='Action time'),
        ),
        migrations.AlterField(
            model_name='managementaction',
            name='duration',
            field=models.DurationField(blank=True, null=True, verbose_name='Duration'),
        ),
        migrations.AlterField(
            model_name='managementaction',
            name='outcome',
            field=models.CharField(choices=[('FD', 'Full destruction, no debris'), ('PD', 'Partial destruction/debris left'), ('ND', 'Empty nest, nothing done')], max_length=2, verbose_name='Outcome'),
        ),
        migrations.AlterField(
            model_name='managementaction',
            name='person_name',
            field=models.CharField(blank=True, max_length=255, verbose_name='Person name'),
        ),
        migrations.AlterField(
            model_name='nest',
            name='address',
            field=models.CharField(blank=True, max_length=255, verbose_name='Address'),
        ),
        migrations.AlterField(
            model_name='nest',
            name='comments',
            field=models.TextField(blank=True, verbose_name='Comments'),
        ),
        migrations.AlterField(
            model_name='nest',
            name='inaturalist_id',
            field=models.BigIntegerField(blank=True, null=True, verbose_name='iNaturalist ID'),
        ),
        migrations.AlterField(
            model_name='nest',
            name='inaturalist_species',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='iNaturalist species'),
        ),
        migrations.AlterField(
            model_name='nest',
            name='latitude',
            field=models.FloatField(verbose_name='Latitude'),
        ),
        migrations.AlterField(
            model_name='nest',
            name='longitude',
            field=models.FloatField(verbose_name='Longitude'),
        ),
        migrations.AlterField(
            model_name='nestpicture',
            name='image',
            field=models.ImageField(upload_to=vespawatch.models.NestPicture.get_file_path, verbose_name='Photo'),
        ),
        migrations.AlterField(
            model_name='taxon',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Scientific name'),
        ),
        migrations.AlterField(
            model_name='taxon',
            name='vernacular_name',
            field=models.CharField(blank=True, max_length=100, verbose_name='Vernacular name'),
        ),
        migrations.AlterField(
            model_name='taxon',
            name='vernacular_name_en',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Vernacular name'),
        ),
        migrations.AlterField(
            model_name='taxon',
            name='vernacular_name_nl',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Vernacular name'),
        ),
    ]
