# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='year',
            name='panel_name',
            field=models.CharField(max_length=75, null=True, blank=True),
        ),
    ]
