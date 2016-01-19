# -*- coding: utf-8 -*-

###########################################
# Django models fields, etc.
from django.db import models

###########################################
# Users
from django.contrib.auth.models import User

###########################################
# Timezone methods
from django.utils import timezone

###########################################
# Global settings
from django.conf import settings

###########################################
# Used to MD5 computation
import hashlib

###########################################
# Used in module load and inspections
import importlib
import inspect
import sys

###########################################
# Middleware used to get current user
from cuser.middleware import CuserMiddleware

from django.contrib import admin

########################################################################
## Computes a checksum from an unicode or str.
def checksum(value):
	if type(value) == str:
		md5_value = hashlib.md5(value).hexdigest()
	else:
		md5_value = hashlib.md5(value.encode("utf-8")).hexdigest()
	return md5_value

########################################################################
## Languages
MODELTRANSLATION_LANG_CHOICES = settings.LANGUAGES

########################################################################################################################
## Gets the name of a translated attribute
def trans_attr(attr, lang):
	"""
	Returns the name of the translated attribute of the object <attribute>_<lang_iso_code>.
	For example: name_es (name attribute in Spanish)
	@param attr Attribute whose name will form the name translated attribute.
	@param lang ISO Language code that will be the suffix of the translated attribute.
	@return: string with the name of the translated attribute.
	"""
	lang = lang.replace("-","_").lower()
	return "{0}_{1}".format(attr,lang)


########################################################################################################################
## Gets the name of a fuzzy (incomplete) translated attribute
def trans_is_fuzzy_attr(attr,lang):
	"""
	Returns the name of the translated  is_fuzzy attribute: <attribute>_is_fuzzy_<lang_iso_code>.
	For example: name_is_fuzzy_es (is fuzzy name attribute in Spanish?)
	@param attr Attribute whose name will form the name translated attribute.
	@param lang ISO Language code that will be the suffix of the translated attribute.
	@return: string with the name of the translated attribute.
	"""
	return "{0}_is_fuzzy".format(trans_attr(attr,lang))


########################################################################
## Each one of the fields that is going to be translated in database
class FieldTranslation(models.Model):

	# Translatable modules (needs to be defined in settings.py)
	_model_module_paths = settings.TRANSLATABLE_MODEL_MODULES

	# Module cache, used to avoid importing several times the same module
	_modules = {}

	# Model cache that avoids importing more than once a Model
	_models = {}

	## Name of the Python module containing the model
	module = models.CharField(max_length=128, verbose_name=u"Module name", help_text=u"Module name that contains the model whose field is translated")

	## Name of the model whose field is translated
	model = models.CharField(max_length=128, verbose_name=u"Model name", help_text=u"Model name whose field is translated")

	## ID of the object whose field is translated
	object_id = models.PositiveIntegerField(default=1, verbose_name=u"Object id", help_text=u'Object id whose field is translated')

	## Name of the field that is going to be translated
	field = models.CharField(max_length=128, verbose_name=u"Object field", help_text=u'Name of the field that is translated')

	## Language used in the translation
	lang = models.CharField(max_length=16, choices=MODELTRANSLATION_LANG_CHOICES, verbose_name=u"Language Id", help_text=u'Language ISO code of this translation')

	## Source text
	source_text = models.TextField(verbose_name=u"Source text", help_text=u"Source text in default language")

	## MD5 of the source text (used to test changes)
	source_md5 = models.CharField(max_length=128, verbose_name=u"MD5 source text", help_text=u"MD5 checksum of source text")

	## Translation of the source_text
	translation = models.TextField(default=None, null=True, verbose_name=u"Translation", help_text=u"Translation showed to users in website when showing it in choosed language.")

	## Needs review? If True, it implies translation is not complete and will not be used.
	is_fuzzy = models.BooleanField(default=False, verbose_name=u"¿Needs reviewing?", help_text=u"This translation needs some reviewing.")

	## Context information that will help translators
	context = models.TextField(default=None, null=True, verbose_name=u"Context", help_text=u"Help context that will be helpful for translators.")

	## Creation date and time of the translation
	creation_datetime = models.DateTimeField(verbose_name=u"Creation date and time of this translation")

	## Last update date and time of the translation
	last_update_datetime = models.DateTimeField(verbose_name=u"Last update date and time of this translation")

	## Creator user
	creator_user = models.ForeignKey(User, null=True, default=None, related_name='model_translation', verbose_name=u"User translator", help_text=u"User that created last translation version")

	## Metainformation of FieldTranslation
	class Meta:
		verbose_name = u"model object field translation"
		verbose_name_plural = u"model object field translations"
		index_together = [
		    ["module", "model", "object_id", "lang", "field", "is_fuzzy"],
		    ["lang", "is_fuzzy"],
			["source_md5"]
		]


	####################################################################################################################
	## Conversion of an object FieldTranslation to unicode
	def __unicode__(self):
		is_fuzzy_text = "*" if self.is_fuzzy else ""
		return u"{0} {1}-{2}-{3}-{4}-'{5}'-'{6}'{7}".format(self.id,self.model,self.object_id,self.field,self.lang,self.source_text,self.translation,is_fuzzy_text)


	####################################################################################################################
	## Conversion of an object FieldTranslation to str
	def __str__(self):
		is_fuzzy_text = "*" if self.is_fuzzy else ""
		return "{0}-{1}-{2}-{3}-'{4}'-'{5}'{6}".format(self.model,self.object_id,self.field,self.lang,self.source_text,self.translation,is_fuzzy_text)


	####################################################################################################################
	## Caching of translatable modules
	@staticmethod
	def _init_module_cache():
		"""
		Module caching, it helps with not having to import again and again same modules.
		@return: boolean, True if module  caching has been done, False if module caching was already done.
		"""

		# While there are not loaded modules, load these ones
		if len(FieldTranslation._modules) < len(FieldTranslation._model_module_paths):
			for module_path in FieldTranslation._model_module_paths:
				FieldTranslation._modules[module_path] = importlib.import_module(module_path)
			return True
		return False


	####################################################################################################################
	## Gets the Python module associated to this field translation
	def get_python_module(self):
		if not self.module in FieldTranslation._modules:
			FieldTranslation._modules[self.module] = importlib.import_module(self.module)
		return FieldTranslation._modules[self.module]


	####################################################################################################################
	## Loads source model in a dynamic attribute in this object
	def _load_source_model(self):
		"""
		Loads and gets the source model of the FieldTranslation as a dynamic attribute. It is used only when deleting
		orphan translations (translations without a parent object associated).
		"""

		# If source_model exists, return it
		if hasattr(self, "source_model"):
			return self.source_model

		# Getting the source model
		module = self.get_python_module()

		# Test if module has inside the model we are looking for
		if hasattr(module, self.model):
			# Setting of source model
			self.source_model = getattr(module, self.model)
			# Setting of verbose name and its plural for later use
			self.source_model.meta__verbose_name = self.source_model._meta.verbose_name
			self.source_model.meta__verbose_name_plural = self.source_model._meta.verbose_name_plural
			return self.source_model
		
		raise ValueError(u"Model {0} does not exist in module".format(self.model, self.module))


	####################################################################################################################
	## Loads source object in a dynamic attribute in this object
	def _load_source_object(self):
		"""
		Loads related object in a dynamic attribute and returns it.
		"""
		if hasattr(self, "source_obj"):
			self.source_text = getattr(self.source_obj, self.field)
			return self.source_obj

		self._load_source_model()
		self.source_obj = self.source_model.objects.get(id=self.object_id)
		return self.source_obj


	####################################################################################################################
	## Delete orphan translations (translations that have no parent object)
	@staticmethod
	def delete_orphan_translations(condition=None):
		"""
		Delete orphan translations.
		This method needs refactoring to be improve its performance.
		"""
		if condition is None:
			condition = {}
		# TODO: optimize using one SQL sentence
		translations = FieldTranslation.objects.all()
		for translation in translations:
			translation._load_source_model()
			condition["id"] = translation.object_id
			if not translation.source_model.objects.filter(**condition).exists():
				translation.delete()


	####################################################################################################################
	## Creates new entries in FieldTranslations table based on new objects not yet inserted
	@staticmethod
	def update_translations(condition=None):
		"""
		Updates FieldTranslations table
		"""
		if condition is None:
			condition = {}

		# Number of updated translations
		num_translations = 0
		
		# Module caching
		FieldTranslation._init_module_cache()

		# Current languages dict
		LANGUAGES = dict(lang for lang in MODELTRANSLATION_LANG_CHOICES)
		if settings.LANGUAGE_CODE in LANGUAGES:
			del LANGUAGES[settings.LANGUAGE_CODE]

		# For each module, we are going to update the translations
		for key in FieldTranslation._modules.keys():
			module = FieldTranslation._modules[key]

			# Class of the module
			clsmembers = inspect.getmembers(sys.modules[key], inspect.isclass)
			for cls in clsmembers:
				cls = cls[1]

				# If the model has in Meta "translatable_fields", we insert this fields
				if hasattr(cls,"_meta") and not cls._meta.abstract and hasattr(cls._meta,"translatable_fields") and len(cls._meta.translatable_fields)>0:
					objects = cls.objects.filter(**condition)
					
					# For each object, language and field are updated
					for obj in objects:
						for lang in LANGUAGES.keys():
							for field in cls._meta.translatable_fields:
								if FieldTranslation.update(obj=obj, field=field, lang=lang, context=""):
									num_translations += 1
		return num_translations


	####################################################################################################################
	## Returns source object
	def get_source_obj(self):
		"""
		Returns source object.
		"""
		return self._load_source_object()


	####################################################################################################################
	## Returns source model
	def get_source_model(self):
		"""
		Returns source model
		"""
		return self._load_source_model()


	####################################################################################################################
	## Returns source model field name
	def get_verbose_field_name(self):
		self._load_source_model()
		try:
			verbose_field_name = self.source_model._meta.get_field_by_name(self.field)[0].verbose_name
			return verbose_field_name
		except:
			return u"Error loading field name"


	####################################################################################################################
	## Constructs a new FieldTranslation object
	@staticmethod
	def factory(obj, field, source_text, lang, context=""):
		"""
		Static method that constructs a translation based on its contents.
		"""

		# Model name
		obj_classname = obj.__class__.__name__

		# Module name
		obj_module = obj.__module__
		
		# Computation of MD5 of the source text
		source_md5 = checksum(source_text)

		# Translated text
		translation = ""

		# Translation text attribute name
		field_lang = trans_attr(field,lang)

		# If in source object there is a translation and is not empty, we asume it was assigned and it's correct
		if hasattr(obj,field_lang) and getattr(obj,field_lang)!="":
			translation = getattr(obj,field_lang)

		# Is the translation fuzzy?
		is_fuzzy = True
		is_fuzzy_lang = trans_is_fuzzy_attr(field,lang)
		if hasattr(obj,is_fuzzy_lang):
			is_fuzzy = getattr(obj,is_fuzzy_lang)

		# Construction of the translation
		trans = FieldTranslation(module=obj_module, model=obj_classname, object_id=obj.id,
		                         field=field, lang=lang, source_text=source_text, source_md5=source_md5,
		                         translation=translation, is_fuzzy=is_fuzzy, context=context)
		return trans


	####################################################################################################################
	## Updates this translation
	def _update(self, obj, field, source_text, context=""):
		#### Update 1: "is_fuzzy" update
		# is_fuzzy field
		lang = self.lang
		is_fuzzy = False
		is_fuzzy_lang = trans_is_fuzzy_attr(field,lang)
		# If source object has is_fuzzy_lang attribute for this field, we get it
		if hasattr(obj, is_fuzzy_lang):
			is_fuzzy = getattr(obj, is_fuzzy_lang)
			self.is_fuzzy = is_fuzzy

		#### Update 2: Update object
		# Source text and source MD5
		self.source_text = source_text
		self.source_md5 = checksum(source_text)

		# Translated text
		# Maybe source object has the translated text. In that case, we get it
		field_lang = trans_attr(field,lang)
		if hasattr(obj,field_lang):
			translation = getattr(obj, field_lang)
			# Is the translation different? In that case, changes the context
			if self.translation != translation:
				self.context = context
			# Translation is alway updated
			self.translation = translation

		# If translation is empty, is_fuzzy must be True always.
		# We don't want to show empty translations in our website
		if self.translation == "":
			self.is_fuzzy = True
		
		self.save()
		return self


	####################################################################################################################
	## Updates a translation
	@staticmethod
	def update(obj, field, lang, context=""):
		try:
			# Class name
			obj_classname = obj.__class__.__name__
			# Module name
			obj_module = obj.__module__
			# Updating of the translation
			trans = FieldTranslation.objects.get(module=obj_module, model=obj_classname, object_id=obj.id, field=field, lang=lang)
			return trans._update(obj=obj, field=field, source_text=getattr(obj,field), context=context)

		# In case the translation does not exist, create a new one
		except FieldTranslation.DoesNotExist:
			source_text = getattr(obj,field)
			# Updates translation only when attribute is a string
			if not source_text is None:
				trans = FieldTranslation.factory(obj=obj, field=field, source_text=getattr(obj,field), lang=lang, context=context)
				return trans._update(obj=obj, field=field, source_text=getattr(obj,field), context=context)
			return False


	####################################################################################################################
	## Save object in database, updating the datetimes accordingly
	def save(self, *args, **kwargs):
		"""
		Save object in database, updating the datetimes accordingly.
		
		"""
		# Now in UTC
		now_datetime = timezone.now()

		# If we are in a creation, assigns creation_datetime
		if not self.id:
			self.creation_datetime = now_datetime

		# Las update datetime is always updated
		self.last_update_datetime = now_datetime
		
		# Current user is creator
		# (get current user with django-cuser middleware)
		self.creator_user = None
		current_user = CuserMiddleware.get_user()
		if not current_user is None and not current_user.is_anonymous():
			self.creator_user_id = current_user.id
		
		# Parent constructor call
		super(FieldTranslation, self).save(*args, **kwargs)


# Admin registration of FieldTranslation model
admin.site.register(FieldTranslation)