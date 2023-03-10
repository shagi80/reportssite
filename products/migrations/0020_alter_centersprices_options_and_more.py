# Generated by Django 4.0.4 on 2022-06-09 07:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0019_alter_centersprices_group'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='centersprices',
            options={'ordering': ['service_center', 'product', 'group', 'code'], 'verbose_name': 'Индивидуальная расценка>', 'verbose_name_plural': 'Индивидуальные расценки'},
        ),
        migrations.AlterField(
            model_name='centersprices',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_parent_group', to='products.codes', verbose_name='Группа дефектов'),
        ),
    ]
