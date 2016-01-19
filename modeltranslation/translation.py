# -*- coding: utf-8 -*-

from modeltranslation.models import checksum, FieldTranslation, trans_attr, trans_is_fuzzy_attr
from django.db import models
from django.db.models import signals
from django.conf import settings
from django.utils import translation
import sys
import inspect


########################################################################
########################################################################
#	ATENCIÓN, LÉEME:
#	Instrucciones:
#	1.	Añadir "from modeltranslation.translation import addtranslations"
#		en los modelos de tu aplicación.
#	2.	Añade a cada modelo de tu aplicación un campo translatable_fields
#		en el Meta con una lista de los atributos a traducir.
#	3.	Realiza esta llamada al FINAL del archivo de modelos:
#		addtranslations(__name__)
########################################################################
########################################################################

########################################################################
########################################################################
#	WARNING, README FIRST:
#	Instructions:
#	1.	Add "from modeltranslation.translation import addtranslations"
#		in your application models.
#	2.	Add to each model you want to translate a new field in Meta with
#		the name "translatable_fields". This field must contain a list
#       of fields that needs to be translated.
#	3.	Call this function AT THE END of your models.py:
#		addtranslations(__name__)
########################################################################
########################################################################


########################################################################
## Add a new field to Meta options "translatable_fields"
models.options.DEFAULT_NAMES += ('translatable_fields',)


########################################################################
## Returns True if there is only one language in this website
def site_is_monolingual():
	return (hasattr(settings, "IS_MONOLINGUAL") and settings.IS_MONOLINGUAL) or len(settings.LANGUAGES)==0


########################################################################
## Adds a signal that will be triggered when saving a model object
def _save_translations(sender, instance, *args, **kwargs):
	"""
	This signal saves model translations.
	"""
	
	# If we are in a site with one language there is no need of saving translations
	if site_is_monolingual():
		return False

	cls = sender

	# If its class has no "translatable_fields" then there are no translations
	if not hasattr(cls._meta, "translatable_fields"):
		return False

	# For each translatable field, get its value, computes its md5 and for each language creates its
	# empty translation.
	for field in cls._meta.translatable_fields:
		value = getattr(instance,field)
		if not value is None:
			md5_value = checksum(value)
			setattr( instance, u"md5"+field, md5_value )
			for lang in settings.LANGUAGES:
				lang = lang[0]
				# print "({0}!={1}) = {2}".format(lang, settings.LANGUAGE_CODE,lang!=settings.LANGUAGE_CODE)
				if lang != settings.LANGUAGE_CODE:
					context = u"Updating from object"
					if hasattr(instance, "trans_context"):
						context = getattr(instance, "trans_context")
					trans = FieldTranslation.update(instance, field, lang, context)


########################################################################
########################################################################
########################################################################
## GET TRANSLATIONS ##


########################################################################################################################
## Get translated fields
def _get_fieldtranslations(instance, field=None, lang=None):
	"""
	Get all the translations for this object.
	"""

	# Basic filtering: filter translations by module, model an object_id
	_filter = {"module": instance.__module__, "model": instance.__class__.__name__, "object_id": instance.id}

	if lang:
		_filter["lang"] = lang

	# If we specify a field we get ONE translation (this field translation)
	if field:
		_filter["field"] = field
		try:
			return FieldTranslation.objects.get(**_filter)
		except FieldTranslation.DoesNotExist:
			return False

	# Otherwise, we get all translations
	return FieldTranslation.objects.filter(**_filter)


########################################################################################################################
## Load translations of an instance
def _load_translations(instance, lang=None):
	"""
	Loads all translations as dynamic attributes:
		<attr>_<lang_code>
		<attr>_<lang_code>_is_fuzzy
	"""
	# Gets field translations
	translations = _get_fieldtranslations(instance=instance, lang=lang)
	for translation_i in translations:
		# Sets translated field lang for this language
		field_lang = trans_attr(translation_i.field, translation_i.lang)
		setattr(instance, field_lang, translation_i.translation)
		# Sets is_fuzzy value for this language
		field_isfuzzy_lang = trans_is_fuzzy_attr(translation_i.field, translation_i.lang)
		#print "{0} ({1}), attr_name={2} value={3}".format(translation.field, translation.lang, isfuzzy_lang,translation.is_fuzzy)
		setattr(instance, field_isfuzzy_lang, translation_i.is_fuzzy)
	return True


########################################################################################################################
## Sets translations from a dict. Used in ModelForms
def _set_dict_translations(instance, dict_translations):
	"""
	Establece los atributos de traducciones a partir de una dict que
	contiene todas las traducciones.
	"""

	# If class has no translatable fields get out
	if not hasattr(instance._meta, "translatable_fields"):
		return False

	# If we are in a site with one language there is no need of saving translations
	if site_is_monolingual():
		return False

	# Translatable fields
	translatable_fields = instance._meta.translatable_fields

	# For each translatable field and for each language (excluding default language), we have to see if there is
	# two dynamic fields:
	# - <attribute>_<language_code>: translated atribute in <language_code>.
	#   For example: name_fr, name_es, description_it, etc.
	# - <attribute>_is_fuzzy_<language_code>: is a provisional translation of <attribute> for language <language_code>.
	#   For example: name_is_fuzzy_fr, name_is_fuzzy_es, description_is_fuzzy_it, etc.
	for field in translatable_fields:
		for lang in settings.LANGUAGES:
			lang = lang[0]
			if lang != settings.LANGUAGE_CODE:
					
				# Translated field name
				trans_field = trans_attr(field,lang)
				# If translated field name is in the dict, we assign it to the object
				if dict_translations.has_key(trans_field):
					setattr(instance,trans_field,dict_translations[trans_field])
					
				# Is fuzzy attribute
				trans_isfuzzy = trans_is_fuzzy_attr(field,lang)
				# If "is fuzzy" name is in the dict, we assign it to the object
				if dict_translations.has_key(trans_isfuzzy):
					is_fuzzy_value = (dict_translations[trans_isfuzzy]=="1") or (dict_translations[trans_isfuzzy]==1)
					setattr(instance,trans_isfuzzy, is_fuzzy_value)


########################################################################
## Gets the translated field of an instance
def _get_translated_field(instance, attr):
	# If we don't have translations, return the original attribute
	if site_is_monolingual():
		return getattr(instance, attr)
	
	# Current language
	lang = translation.get_language()
	#print u"\n{0}[id={1}]: {2}='{3}', atrr_in_lang='{2}_{4}'".format(instance.__class__.__name__, instance.id, attr, getattr(instance,attr), lang)
	
	# Load translations
	_load_translations(instance=instance, lang=lang)
	
	# Names of translated attributes of translated attribute and related is_fuzzy one.
	trans_field = trans_attr(attr, lang)
	is_fuzzy_attr = trans_is_fuzzy_attr(attr, lang)
	
	# If the translated attribute exists and is not fuzzy, return it
	if hasattr(instance,trans_field) and hasattr(instance, is_fuzzy_attr) and not getattr(instance, is_fuzzy_attr):
		return getattr(instance,trans_field)
	
	# Otherwise, return its original value
	return getattr(instance, attr)


########################################################################
########################################################################
########################################################################
## HANDLERS ##


########################################################################
## Adds the actions to a class
def add_translation(sender):
	"""
	Adds the actions to a class.
	"""
	# 1. Execute _save_translations when saving an object
	signals.post_save.connect(_save_translations, sender=sender)
	# 2. Adds get_fieldtranslations to class. Remember that this method get all the translations.
	sender.add_to_class("get_fieldtranslations", _get_fieldtranslations)
	# 3. Adss load_translations. Remember that this method included all the translations as dynamic attributes.
	sender.add_to_class("load_translations", _load_translations)
	# 4. Adds _set_dict_translations. This methods allows us setting all the translated fields form a dict.
	# Very useful when dealing with ModelForms.
	sender.add_to_class("set_translation_fields", _set_dict_translations)
	# 5. This methods returns one translated attribute in Django.
	# Avoid using _ and use get_trans_attr because Django maketranslations parser is fooled believing that everything
	# inside _ methods is translatable.
	sender.add_to_class("_", _get_translated_field)
	sender.add_to_class("get_trans_attr", _get_translated_field)
	sender.add_to_class("_t", _get_translated_field)


########################################################################
## Adds translation actions to a module
def addtranslations(module=__name__):
	# For each class in that module
	clsmembers = inspect.getmembers(sys.modules[module], inspect.isclass)
	for cls in clsmembers:
		cls = cls[1]
		# If this class has translatable fields, add actions to it
		if hasattr(cls,"_meta") and not cls._meta.abstract and hasattr(cls._meta,"translatable_fields") and len(cls._meta.translatable_fields)>0:
			add_translation(cls)


