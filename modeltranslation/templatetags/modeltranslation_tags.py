# -*- coding: utf-8 -*-

from django import template
from django.conf import settings
from django.utils.translation import get_language

from modeltranslation.translation import _get_fieldtranslations

register = template.Library()

## Caché global en la que almacenar los objetos con sus traducciones
## para disminuir los accesos a BD
#CACHE = {}


########################################################################
## Obtiene la traducción del atributo en el idioma actual
## Ejecuta una llamada al sistema de traducciones de forma que
## realizando una llamada {{ <obj>|_:"<attr>" }} se traduce el atributo
## de forma automática. Por ejemplo: {{ event|_:"name" }}
def get_translated_attribute(instance, attr):
	"""
	Envuelve el __getattribute__ de los modelos de Django
	con el objetivo de hacer la traducción "less painful"
	"""
	
	#print u"get_translated_attribute {0}[id={1}].{2}".format(instance.__class__.__name__, instance.id, attr)
	
	# Si no tiene atributos traducibles o existe pero la lista está vacía,
	# devolvemos el atributo normal
	try:
		if not hasattr(instance._meta, "translatable_fields") or len(getattr(instance._meta,"translatable_fields"))==0:
			#print "No tiene el atributo {0}".format(attr)
			return getattr(instance, attr)
	except AttributeError:
		return instance
	
	# Atributos traducibles
	translatable_fields = instance._meta.translatable_fields

	# Lenguaje actual
	cur_language = get_language()
	lang = cur_language.title().lower()
	
	#print "Lang es {0}".format(lang)
	
	# Si el idioma actual es predeterminado, el mismo atributo almacena
	# el contenido que nos interesa y FIN
	if lang == settings.LANGUAGE_CODE:
		#print "{0} == {1}? {2}".format(lang, settings.LANGUAGE_CODE, lang == settings.LANGUAGE_CODE)
		return getattr(instance, attr)
	
	#cache = TransCache.factory()
	#if not cache.has(lang, instance):
		#cache.set(lang, instance)
	#instance = cache.get(lang, instance)
	
	# Comprobamos si el atributo es de los que han de traducirse
	# Si no es así, obtenemos el atributo normal y FIN
	if not attr in translatable_fields:
		#print "El atributo no ha de traducirse"
		return getattr(instance, attr)

	# Atributos derivados de attr y del idioma actual
	#t_attr = trans_attr(attr,lang)
	#t_attr_isfuzzy = trans_is_fuzzy_attr(attr,lang)

	# Obtenemos la traducción del campo directamente, sin usar cachés
	# Ni chorradas varias, debido a que queremos que esto funcione de
	# una vez
	field_translation = _get_fieldtranslations(instance, field=attr, lang=lang)
	if field_translation:
		if not field_translation.is_fuzzy:
			return field_translation.translation
	return getattr(instance, attr)


# Llamada al registrador de las plantillas, para añadir este filtro
register.filter('_', get_translated_attribute)
