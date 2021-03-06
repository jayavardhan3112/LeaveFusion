# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-10 23:46
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('user_app', '0001_initial'),
        ('leave_application', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaveMigration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('add', 'Add'), ('del', 'Delete')], default='add', max_length=10)),
                ('start_date', models.DateField(blank=True)),
                ('end_date', models.DateField(blank=True)),
                ('replacement_type', models.CharField(default='academic', max_length=20)),
                ('rep', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_app.Replacement')),
                ('replacee', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='to_be_migrated', to=settings.AUTH_USER_MODEL)),
                ('replacer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='to_be_migrated_rep', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MigrationChangeDate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_date_change', models.DateField()),
            ],
        ),
    ]
