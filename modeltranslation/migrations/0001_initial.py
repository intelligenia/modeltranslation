# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FieldTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model', models.CharField(max_length=128, verbose_name='Modelo a traducir')),
                ('object_id', models.PositiveIntegerField(default=1, help_text='Id del objeto traducido', verbose_name='Id del objeto')),
                ('field', models.CharField(help_text='Campo origen cuyo texto ha sido traducido', max_length=128, verbose_name='Campo origen')),
                ('lang', models.CharField(help_text='Idioma de la traducci\xf3n', max_length=16, verbose_name='Id del idioma', choices=[(b'af', b'Afrikaans'), (b'ar', b'Arabic'), (b'ast', b'Asturian'), (b'az', b'Azerbaijani'), (b'bg', b'Bulgarian'), (b'be', b'Belarusian'), (b'bn', b'Bengali'), (b'br', b'Breton'), (b'bs', b'Bosnian'), (b'ca', b'Catalan'), (b'cs', b'Czech'), (b'cy', b'Welsh'), (b'da', b'Danish'), (b'de', b'German'), (b'el', b'Greek'), (b'en', b'English'), (b'en-au', b'Australian English'), (b'en-gb', b'British English'), (b'eo', b'Esperanto'), (b'es', b'Spanish'), (b'es-ar', b'Argentinian Spanish'), (b'es-mx', b'Mexican Spanish'), (b'es-ni', b'Nicaraguan Spanish'), (b'es-ve', b'Venezuelan Spanish'), (b'et', b'Estonian'), (b'eu', b'Basque'), (b'fa', b'Persian'), (b'fi', b'Finnish'), (b'fr', b'French'), (b'fy', b'Frisian'), (b'ga', b'Irish'), (b'gl', b'Galician'), (b'he', b'Hebrew'), (b'hi', b'Hindi'), (b'hr', b'Croatian'), (b'hu', b'Hungarian'), (b'ia', b'Interlingua'), (b'id', b'Indonesian'), (b'io', b'Ido'), (b'is', b'Icelandic'), (b'it', b'Italian'), (b'ja', b'Japanese'), (b'ka', b'Georgian'), (b'kk', b'Kazakh'), (b'km', b'Khmer'), (b'kn', b'Kannada'), (b'ko', b'Korean'), (b'lb', b'Luxembourgish'), (b'lt', b'Lithuanian'), (b'lv', b'Latvian'), (b'mk', b'Macedonian'), (b'ml', b'Malayalam'), (b'mn', b'Mongolian'), (b'mr', b'Marathi'), (b'my', b'Burmese'), (b'nb', b'Norwegian Bokmal'), (b'ne', b'Nepali'), (b'nl', b'Dutch'), (b'nn', b'Norwegian Nynorsk'), (b'os', b'Ossetic'), (b'pa', b'Punjabi'), (b'pl', b'Polish'), (b'pt', b'Portuguese'), (b'pt-br', b'Brazilian Portuguese'), (b'ro', b'Romanian'), (b'ru', b'Russian'), (b'sk', b'Slovak'), (b'sl', b'Slovenian'), (b'sq', b'Albanian'), (b'sr', b'Serbian'), (b'sr-latn', b'Serbian Latin'), (b'sv', b'Swedish'), (b'sw', b'Swahili'), (b'ta', b'Tamil'), (b'te', b'Telugu'), (b'th', b'Thai'), (b'tr', b'Turkish'), (b'tt', b'Tatar'), (b'udm', b'Udmurt'), (b'uk', b'Ukrainian'), (b'ur', b'Urdu'), (b'vi', b'Vietnamese'), (b'zh-cn', b'Simplified Chinese'), (b'zh-hans', b'Simplified Chinese'), (b'zh-hant', b'Traditional Chinese'), (b'zh-tw', b'Traditional Chinese')])),
                ('source_text', models.TextField(verbose_name='Texto origen.')),
                ('source_md5', models.CharField(max_length=128, verbose_name='MD5 del texto origen.')),
                ('translation', models.TextField(default=None, help_text='Texto de la traducci\xf3n que se mostrar\xe1 al usuario cuando seleccione el idioma actual.', null=True, verbose_name='Traducci\xf3n')),
                ('is_fuzzy', models.BooleanField(default=False, help_text='Esta traducci\xf3n ha de ser revisada por un traductor.', verbose_name='\xbfRequiere revisi\xf3n?')),
                ('context', models.TextField(default=None, help_text='Contexto que ayudar\xe1 a los traductores a traducir este texto.', null=True, verbose_name='Contexto')),
                ('creation_datetime', models.DateTimeField(verbose_name='Fecha de creaci\xf3n del objeto')),
                ('last_update_datetime', models.DateTimeField(verbose_name='Fecha de \xfaltima actualizaci\xf3n del objeto')),
                ('creator_user', models.ForeignKey(related_name='model_translation', default=None, to=settings.AUTH_USER_MODEL, help_text='Usuario que ha realizado la \xfaltima traducci\xf3n', null=True, verbose_name='Usuario que ha realizado la traducci\xf3n')),
            ],
        ),
    ]
