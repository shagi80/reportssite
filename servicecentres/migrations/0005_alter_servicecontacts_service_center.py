# Generated by Django 4.0.4 on 2022-05-29 17:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('servicecentres', '0004_alter_servicecontacts_service_center'),
    ]

    operations = [
        migrations.AlterField(
            model_name='servicecontacts',
            name='service_center',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servicecentres.servicecenters', verbose_name='Сервисный центр'),
        ),
    ]