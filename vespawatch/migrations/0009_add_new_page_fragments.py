# Generated by Django 2.1.5 on 2019-02-12 15:10

from django.db import migrations

NEW_PAGE_FRAGMENTS_IDS = ['about_project_page', 'about_activities_page', 'about_vespavelutina_page',
                          'about_management_page', 'about_privacypolicy_page', 'about_links_page']

def delete_pagefragments(apps, schema_editor):
    PageFragment = apps.get_model('page_fragments', 'PageFragment')

    for identifier in NEW_PAGE_FRAGMENTS_IDS:
        try:
            PageFragment.objects.get(identifier=identifier).delete()
        except:
            pass

def create_pagefragments(apps, schema_editor):
    PageFragment = apps.get_model('page_fragments', 'PageFragment')


    for identifier in NEW_PAGE_FRAGMENTS_IDS:
        PageFragment.objects.update_or_create(
            identifier=identifier,
            defaults={'content_nl': f'NL content for {identifier}',
                      'content_en': f'EN content for {identifier}'},
        )

class Migration(migrations.Migration):

    dependencies = [
        ('vespawatch', '0008_auto_20190128_1524'),
    ]

    operations = [
        migrations.RunPython(create_pagefragments, delete_pagefragments),
    ]
