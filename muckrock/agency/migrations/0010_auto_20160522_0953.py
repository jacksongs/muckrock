# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-22 09:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0009_add_agency_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agency',
            name='users',
            field=models.ManyToManyField(related_name='agencies', through='agency.AgencyProfile', to='accounts.AgencyUser'),
        ),
        migrations.AlterField(
            model_name='agencyprofile',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.AgencyUser'),
        ),
    ]
