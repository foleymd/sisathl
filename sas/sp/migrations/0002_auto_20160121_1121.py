# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('sp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='athleteccyyssport',
            name='sport_description',
            field=models.CharField(max_length=60, blank=True),
        ),
        migrations.AlterField(
            model_name='ccyysadmin',
            name='athletics_close_date',
            field=models.DateField(default=datetime.date(9999, 12, 31)),
        ),
        migrations.AlterField(
            model_name='ccyysadmin',
            name='athletics_open_date',
            field=models.DateField(default=datetime.date(9999, 12, 31)),
        ),
        migrations.AlterField(
            model_name='ccyysadmin',
            name='dean_close_date',
            field=models.DateField(default=datetime.date(9999, 12, 31)),
        ),
        migrations.AlterField(
            model_name='ccyysadmin',
            name='dean_open_date',
            field=models.DateField(default=datetime.date(9999, 12, 31)),
        ),
        migrations.AlterField(
            model_name='ccyysadmin',
            name='reg_close_date',
            field=models.DateField(default=datetime.date(9999, 12, 31)),
        ),
        migrations.AlterField(
            model_name='ccyysadmin',
            name='reg_open_date',
            field=models.DateField(default=datetime.date(9999, 12, 31)),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(default=b'', max_length=254, verbose_name=b'email'),
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(max_length=50, verbose_name=b'name'),
        ),
        #migrations.AlterUniqueTogether(
        #    name='athletemajor',
        #    unique_together=set([('school', 'major_code', 'minor', 'catalog_begin', 'athlete_ccyys_admin')]),
        #),
    ]
