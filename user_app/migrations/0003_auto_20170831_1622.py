# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-31 16:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0002_auto_20170831_1523'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extrainfo',
            name='sanctioning_authority',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sanctioning_auth_to', to='user_app.Designation'),
        ),
        migrations.AlterField(
            model_name='extrainfo',
            name='sanctioning_officer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sanctioning_officer_to', to='user_app.Designation'),
        ),
    ]
