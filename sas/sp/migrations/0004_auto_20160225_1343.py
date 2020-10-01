# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp', '0003_auto_20160225_1338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spdformlog',
            name='final_percentage',
            field=models.FloatField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name='spdformlog',
            name='projected_percentage',
            field=models.FloatField(default=0, null=True),
        ),
    ]
