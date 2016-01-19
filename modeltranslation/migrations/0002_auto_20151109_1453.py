# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modeltranslation', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fieldtranslation',
            name='lang',
            field=models.CharField(help_text='Idioma de la traducci\xf3n', max_length=16, verbose_name='Id del idioma', choices=[('es', 'Espa\xf1ol'), ('en', 'English'), ('de', 'Deutsch')]),
        ),
    ]
