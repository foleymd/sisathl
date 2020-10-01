# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0003_auto_20160308_1327'),
    ]

    operations = [
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('survey_id', models.CharField(max_length=50)),
                ('year', models.ForeignKey(to='compliance.Year')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='suvey',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='suvey',
            name='year',
        ),
        migrations.DeleteModel(
            name='Suvey',
        ),
        migrations.AlterUniqueTogether(
            name='survey',
            unique_together=set([('year', 'survey_id')]),
        ),
    ]
