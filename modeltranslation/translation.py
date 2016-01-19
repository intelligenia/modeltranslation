# -*- coding: utf-8 -*-

###########################################
# Importamos los modelos para añadirle un campo a su meta

from modeltranslation.models import checksum, FieldTranslation, trans_attr, trans_is_fuzzy_attr

from django.db import models
# Importamos las señales, para enviar señales después de guardar el objeto
from django.db.models import signals
from django.conf import settings

from django.utils import translation
import hashlib

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
## Añadimos nuevo campo a Meta a todos los modelos
models.options.DEFAULT_NAMES += ('translatable_fields',)


########################################################################
## Añadimos la señal que se añade después de guardar el modelo
def _save_translations(sender, instance, *args, **kwargs):
	"""Esta señal almacena todas las traducciones para idiomas."""
	
	# Si estamos ante un sitio web monolingüe, no hace nada
	if settings.IS_MONOLINGUAL:
		return False

	cls = sender

	# Si no tiene campos traducibles, no hace nada
	if not hasattr(cls._meta, "translatable_fields"):
		return False

	for field in cls._meta.translatable_fields:
		value = getattr(instance,field)
		if not value is None:
			md5_value = checksum(value)
			setattr( instance, u"md5"+field, md5_value )
			for lang in settings.LANGUAGES:
				lang = lang[0]
				#print "({0}!={1}) = {2}".format(lang, settings.LANGUAGE_CODE,lang!=settings.LANGUAGE_CODE)
				if lang != settings.LANGUAGE_CODE:
					#print "Entramos en FieldTranslation.update"
					#print instance.__class__
					#print field
					context = "Actualización desde objeto"
					if hasattr(instance, "trans_context"):
						context = getattr(instance, "trans_context")
					trans = FieldTranslation.update(instance, field, lang, context)
					#print "Salimos en FieldTranslation.update"
	
	# Cada vez que se guarda un objeto, se limpia completamente
	# la caché de traducciones
	#cache = TransCache.factory()
	#cache.clear()


########################################################################
########################################################################
########################################################################
## OBTIENEN TRADUCCIONES ##


########################################################################
## Obtenemos los campos traducidos
def _get_fieldtranslations(instance, field=None, lang=None):
	"""Obtiene todas las traducciones de los campos de este objeto"""
	filter = {"model":instance.__class__.__name__, "object_id":instance.id}
	if lang:
		filter["lang"] = lang
	if field:
		filter["field"] = field
		# Obtiene UNA traducción
		try:
			return FieldTranslation.objects.get(**filter)
		except FieldTranslation.DoesNotExist:
			return False
	# Obtiene TODAS las traducciones
	return FieldTranslation.objects.filter(**filter)


def _load_translations(instance, lang=None):
	"""
	Carga las traducciones como atributos de la forma
		<attr>_<lang_code>
		<attr>_<lang_code>_is_fuzzy
	"""
	# Si queremos todas las traducciones de todos los idiomas
	translations = _get_fieldtranslations(instance=instance, lang=lang)
	for translation in translations:
		# Establecemos el campo traducido
		field_lang = trans_attr(translation.field,translation.lang)
		setattr(instance, field_lang, translation.translation)
		# Establecemos el valor is_fuzzy para ese idioma
		field_isfuzzy_lang = trans_is_fuzzy_attr(translation.field,translation.lang)
		#print "{0} ({1}), attr_name={2} value={3}".format(translation.field, translation.lang, isfuzzy_lang,translation.is_fuzzy)
		setattr(instance, field_isfuzzy_lang, translation.is_fuzzy)
	return True


########################################################################
## Establece las traducciones desde  un diccionario, útil para usarlo
## en el clean de formularios
def _set_dict_translations(instance, dict_translations):
	"""
	Establece los atributos de traducciones a partir de una dict que
	contiene todas las traducciones.
	"""

	# Si no tiene campos traducibles, no hace nada
	if not hasattr(instance._meta, "translatable_fields"):
		return False

	# Evidentemente, no debemos ejecutar nada de esto si estamos en un
	# entorno monolingüe
	if not settings.IS_MONOLINGUAL:
		translatable_fields = instance._meta.translatable_fields
		
		# Para cada uno de los campos traducibles, para cada idioma que
		# no sea el idioma de por defecto, hemos de comprobar si para
		# cada atributo del objeto se tienen dos atributos extra:
		# - Atributo traducido (normalmente con el sufijo _fr, _en, etc.)
		# - Atributo que indica si la traducción es provicional (normalmente con el sufijo _fuzzy_fr, _fuzzy_en, etc.
		for field in translatable_fields:
			for lang in settings.LANGUAGES:
				lang = lang[0]
				if lang != settings.LANGUAGE_CODE:
					
					# Atributo de idioma
					trans_field = trans_attr(field,lang)
					# Si se ha enviado el atributo traducido,
					# lo asignamos al objeto
					if dict_translations.has_key(trans_field):
						setattr(instance,trans_field,dict_translations[trans_field])
					
					# Atributo que indica si es provisional
					trans_isfuzzy = trans_is_fuzzy_attr(field,lang)
					# Si se ha enviado el atributo traducido,
					# lo asignamos al objeto
					if dict_translations.has_key(trans_isfuzzy):
						is_fuzzy_value = (dict_translations[trans_isfuzzy]=="1") or (dict_translations[trans_isfuzzy]==1)
						setattr(instance,trans_isfuzzy, is_fuzzy_value)


########################################################################
## Obtiene un atributo traducido al idioma seleccionado
# Añade el método _ a cada objeto
def _get_translated_field(instance, attr):
	# Si la web es monolingue, obtenemos el atributo tal cual
	if settings.IS_MONOLINGUAL:
		return getattr(instance,attr)
	
	# Obtiene el idioma actual
	lang = translation.get_language()
	#print u"\n{0}[id={1}]: {2}='{3}', atrr_in_lang='{2}_{4}'".format(instance.__class__.__name__, instance.id, attr, getattr(instance,attr), lang)
	
	# Si no ha cargado las traducciones, las carga
	#translation_loaded_flag = "_translations_loaded_{0}".format(lang)
	#if not hasattr(instance,attr) or not hasattr(instance,translation_loaded_flag) or not getattr(instance,translation_loaded_flag):
		#setattr(instance,translation_loaded_flag,True)
		#_load_translations(instance=instance, lang=lang)
	_load_translations(instance=instance, lang=lang)
	
	# Obtenemos el nombre del atributo en el idioma seleccionado
	trans_field = trans_attr(attr, lang)
	is_fuzzy_attr = trans_is_fuzzy_attr(attr, lang)
	
	# Si el atributo existe en ese idioma, lo devolvemos
	if hasattr(instance,trans_field) and hasattr(instance, is_fuzzy_attr) and not getattr(instance, is_fuzzy_attr):
		trans_value = getattr(instance,trans_field)
	
	# Si no existe en ese idioma, devolvemos el valor en el idioma por
	# defecto (que en nuestro caso es español)
	else:
		trans_value = getattr(instance,attr)
	
	#print u"{0}_{1}='{2}'".format(attr, lang, trans_value)
	return trans_value


########################################################################
########################################################################
########################################################################
## MANEJADORES ##


########################################################################
## Añade las acciones de las traducciones para una clase
def add_translation(sender):
	"""
	Añade las acciones de las traducciones para una clase
	"""
	# 1. Señal que avisa cuando el objeto se guarda
	signals.post_save.connect(_save_translations, sender=sender)
	# 2. Método para obtener todas las traducciones
	sender.add_to_class("get_fieldtranslations", _get_fieldtranslations)
	# 3. Método para incluir las traducciones como atributos dinámicos
	sender.add_to_class("load_translations", _load_translations)
	# 4. Método para establecer las traducciones como atributos dinámicos desde diccionario
	sender.add_to_class("set_translation_fields", _set_dict_translations)
	# 5. Métodos que devuelven un atributo traducido según el idioma
	# Teóricamente el método "_" no habría que usarlo porque el analizador
	# de Django es tonto y lo interpreta como ugettext
	sender.add_to_class("_", _get_translated_field)
	sender.add_to_class("get_trans_attr", _get_translated_field)
	sender.add_to_class("_t", _get_translated_field)


########################################################################
## Añade las acciones de traducción de un módulo
def addtranslations(module=__name__):
	"""Añade las acciones de las traducciones de un módulo"""
	import sys
	import inspect
	# Coge todas las clases del módulo
	clsmembers = inspect.getmembers(sys.modules[module], inspect.isclass)
	for cls in clsmembers:
		cls = cls[1]
		# Si tienen cammpos traducibles, le añadimos los métodos
		# que devuelvan los atributos traducidos
		if hasattr(cls,"_meta") and not cls._meta.abstract and hasattr(cls._meta,"translatable_fields") and len(cls._meta.translatable_fields)>0:
			add_translation(cls)


