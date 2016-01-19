# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modeltranslation', '0003_auto_20151211_1232'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='fieldtranslation',
            index_together=set([('source_md5',), ('model', 'object_id', 'lang', 'field', 'is_fuzzy')]),
        ),
    ]
