# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modeltranslation', '0002_auto_20151109_1453'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='fieldtranslation',
            options={'verbose_name': 'traducci\xf3n de campo de un modelo', 'verbose_name_plural': 'traducciones de campos de modelos'},
        ),
        migrations.AlterIndexTogether(
            name='fieldtranslation',
            index_together=set([('source_md5',), ('model', 'object_id', 'field', 'lang', 'is_fuzzy')]),
        ),
    ]
