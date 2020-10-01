# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp', '0002_auto_20160121_1121'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='athletemajor',
            unique_together=set([('school', 'major_code', 'minor', 'catalog_begin', 'athlete_ccyys_admin')]),
        ),
    ]
