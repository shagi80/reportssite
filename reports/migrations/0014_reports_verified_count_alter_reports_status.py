# Generated by Django 4.0.4 on 2022-07-20 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0013_remove_reportsrecords_status_reportsrecords_verified_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reports',
            name='verified_count',
            field=models.IntegerField(default=0, verbose_name='Количестов принятых ремонтов'),
        ),
        migrations.AlterField(
            model_name='reports',
            name='status',
            field=models.CharField(choices=[('draft', 'черновик'), ('send', 'отправлен на проверку'), ('refinement', 'возвращен на доработку'), ('received', 'идет проверка'), ('verified', 'проверка закончена'), ('accepted', 'принят'), ('payment', 'передан в оплату')], default='draft', max_length=100, verbose_name='Статус'),
        ),
    ]