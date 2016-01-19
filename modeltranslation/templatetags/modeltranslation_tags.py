# -*- coding: utf-8 -*-

from django import template
from django.conf import settings
from django.utils.translation import get_language

from modeltranslation.translation import _get_fieldtranslations

register = template.Library()

########################################################################
## Gets current language translations
## allowing developers to call {{ <obj>|_:"<attr>" }} that translates
## attribute <attr> to current language. For example: {{ event|_:"name" }}
def get_translated_attribute(instance, attr):
	"""
	Wraps Django Model __getattribute__ method making translation in templates less painful
	"""
	
	# If its class has no translatable fields, returns attribute
	try:
		if not hasattr(instance._meta, "translatable_fields") or len(getattr(instance._meta,"translatable_fields"))==0:
			return getattr(instance, attr)
	except AttributeError:
		return instance
	
	# Translatable fields of this instance
	translatable_fields = instance._meta.translatable_fields

	# Current language
	cur_language = get_language()
	lang = cur_language.title().lower()

	# If current language is default language, returns attribute
	if lang == settings.LANGUAGE_CODE:
		return getattr(instance, attr)
	
	# Otherwise, if a translation is NOT needed for attr atribute, get attribute
	if not attr in translatable_fields:
		return getattr(instance, attr)

	# Gets field translations of this instance and return the translated attribute
	field_translation = _get_fieldtranslations(instance, field=attr, lang=lang)
	if field_translation:
		if not field_translation.is_fuzzy:
			return field_translation.translation
	return getattr(instance, attr)


# Register this template filter
register.filter('_', get_translated_attribute)
