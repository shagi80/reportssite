# Generated by Django 4.0.4 on 2022-06-26 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_reports_total_cost_alter_reports_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reports',
            name='records_count',
            field=models.IntegerField(default=0, verbose_name='Количестов ремонтов'),
        ),
        migrations.AlterField(
            model_name='reports',
            name='total_cost',
            field=models.FloatField(default=0, verbose_name='Общая сумма по отчету'),
        ),
        migrations.AlterField(
            model_name='reportsrecords',
            name='move_cost',
            field=models.FloatField(blank=True, default=0, verbose_name='За выезд'),
        ),
        migrations.AlterField(
            model_name='reportsrecords',
            name='parts_cost',
            field=models.FloatField(default=0, verbose_name='За детали'),
        ),
        migrations.AlterField(
            model_name='reportsrecords',
            name='total_cost',
            field=models.FloatField(default=0, verbose_name='Всего за ремонт'),
        ),
        migrations.AlterField(
            model_name='reportsrecords',
            name='work_cost',
            field=models.FloatField(default=0, verbose_name='За работу'),
        ),
    ]
