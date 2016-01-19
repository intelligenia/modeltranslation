# -*- coding: utf-8 -*-

from modeltranslation.models import FieldTranslation
import hashlib

###########################################
## Configuraciones del sistema
from django.conf import settings

def _make_translations(obj):
	cls = obj.__class__
	obj.classname = cls.__name__
	if hasattr(cls,"TRANSLATABLE_FIELDS"):
		for field in cls.TRANSLATABLE_FIELDS:
			value = getattr(obj,field)
			md5_value = hashlib.md5(value.encode("utf-8")).hexdigest()
			setattr( obj, "md5"+field, md5_value )
			for lang in settings.LANGUAGES:
				trans = FieldTranslation.update(obj, field, lang[0])


def savetranslation(fn):
	def _make_translations_wrapper(self):
		_make_translations(self)
		fn(self)
	return _make_translations_wrapper

#def trace(cls):
	#for name, m in inspect.getmembers(cls, inspect.ismethod):
		#print cls
		#print "- "cls
		#setattr(cls,name,log(m))
	#return cls
