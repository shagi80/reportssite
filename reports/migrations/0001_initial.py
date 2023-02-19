# Generated by Django 4.0.4 on 2022-06-14 17:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('servicecentres', '0006_alter_servicecontacts_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Reports',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_date', models.DateTimeField(verbose_name='Отчетный период')),
                ('status', models.CharField(choices=[('draft', 'черновик'), ('send', 'отправлен на проверку'), ('refinement', 'возвращен на доработку'), ('received', 'получен'), ('verified', 'проверен'), ('accepted', 'принят'), ('payment', 'передан в оплату')], default='draft', max_length=100, verbose_name='Статус')),
                ('note', models.TextField(blank=True, null=True, verbose_name='Примечание')),
                ('invoice', models.CharField(blank=True, max_length=250, null=True, verbose_name='Реквизиты счета')),
                ('act', models.CharField(blank=True, max_length=250, null=True, verbose_name='Реквизиты акта')),
                ('mail_date', models.DateTimeField(blank=True, null=True, verbose_name='Дата приема корреспонденции')),
                ('service_center', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servicecentres.servicecenters', verbose_name='Сервисный центр')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Автор отчета')),
            ],
            options={
                'verbose_name': 'Отчет',
                'verbose_name_plural': 'Отчеты',
                'ordering': ['report_date', 'service_center', 'status'],
            },
        ),
    ]