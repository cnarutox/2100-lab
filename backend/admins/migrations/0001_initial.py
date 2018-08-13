# Generated by Django 2.1 on 2018-08-13 11:02

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdminLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.SmallIntegerField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('old_data', models.TextField()),
                ('new_data', models.TextField()),
                ('object_id', models.IntegerField()),
            ],
        ),
    ]
