# Generated by Django 4.0.4 on 2022-06-15 19:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_reportsrecords_reportsparts'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reportsrecords',
            name='report_date',
        ),
    ]
