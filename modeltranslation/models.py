# -*- coding: utf-8 -*-

###########################################
# Lo básico sobre los modelos
from django.db import models

###########################################
# Grupos de usuarios
from django.contrib.auth.models import Group, User

###########################################
# Timezone methods
from django.utils import timezone

###########################################
# Preferencias globales
from django.conf import settings

###########################################
# Para el cálculo del md5
import hashlib

###########################################
# Middleware para obtener el usuario actual
from cuser.middleware import CuserMiddleware

########################################################################
## Cálculo del checksum en función de si recibe un str o un unicode
## Python 2.7 tiene el problema de tener dos tipos incompatibles para
## representar cadenas, como vemos aquí.
def checksum(value):
	if type(value) == str:
		md5_value = hashlib.md5(value).hexdigest()
	else:
		md5_value = hashlib.md5(value.encode("utf-8")).hexdigest()
	return md5_value

########################################################################
## Opciones de idioma
MODELTRANSLATION_LANG_CHOICES = settings.LANGUAGES

def trans_attr(attr,lang):
	lang = lang.replace("-","_").lower()
	return "{0}_{1}".format(attr,lang)

def trans_is_fuzzy_attr(attr,lang):
	return "{0}_is_fuzzy".format(trans_attr(attr,lang))

########################################################################
## Translation in DB
class FieldTranslation(models.Model):
	
	_model_module_paths = settings.MODEL_MODULES
	_modules = {}
	_models = {}
	
	model = models.CharField(max_length=128, verbose_name=u"Modelo a traducir")
	object_id = models.PositiveIntegerField(default=1, verbose_name=u"Id del objeto", help_text=u'Id del objeto traducido')
	field = models.CharField(max_length=128, verbose_name=u"Campo origen", help_text=u'Campo origen cuyo texto ha sido traducido')
	lang = models.CharField(max_length=16, choices=MODELTRANSLATION_LANG_CHOICES, verbose_name=u"Id del idioma", help_text=u'Idioma de la traducción')
	
	source_text = models.TextField(verbose_name=u"Texto origen.")
	source_md5 = models.CharField(max_length=128, verbose_name=u"MD5 del texto origen.")
	translation = models.TextField(default=None, null=True, verbose_name=u"Traducción", help_text=u"Texto de la traducción que se mostrará al usuario cuando seleccione el idioma actual.")
	is_fuzzy = models.BooleanField(default=False, verbose_name=u"¿Requiere revisión?", help_text=u"Esta traducción ha de ser revisada por un traductor.")
	context = models.TextField(default=None, null=True, verbose_name=u"Contexto", help_text=u"Contexto que ayudará a los traductores a traducir este texto.")
	
	creation_datetime = models.DateTimeField(verbose_name=u"Fecha de creación del objeto")
	last_update_datetime = models.DateTimeField(verbose_name=u"Fecha de última actualización del objeto")

	## Usuario creador
	creator_user = models.ForeignKey(User, null=True, default=None, related_name='model_translation', verbose_name=u"Usuario que ha realizado la traducción", help_text=u"Usuario que ha realizado la última traducción")

	## Metainformación sobre la foto de evento.
	class Meta:
		verbose_name = "traducción de campo de un modelo"
		verbose_name_plural = "traducciones de campos de modelos"
		index_together = [
		    ["model", "object_id", "lang", "field", "is_fuzzy"],
			["source_md5"]
		]

	def __unicode__(self):
		is_fuzzy_text = "*" if self.is_fuzzy else ""
		return u"{0} {1}-{2}-{3}-{4}-'{5}'-'{6}'{7}".format(self.id,self.model,self.object_id,self.field,self.lang,self.source_text,self.translation,is_fuzzy_text)

	def __str__(self):
		is_fuzzy_text = "*" if self.is_fuzzy else ""
		return "{0}-{1}-{2}-{3}-'{4}'-'{5}'{6}".format(self.model,self.object_id,self.field,self.lang,self.source_text,self.translation,is_fuzzy_text)

	def _load_source_model(self):
		"""Carga el modelo fuente"""
		if hasattr(self, "source_model"):
			return self.source_model
		# Cacheo de los módulos
		import importlib
		if len(FieldTranslation._modules.keys())==0:
			for module_path in FieldTranslation._model_module_paths:
				FieldTranslation._modules[module_path] = importlib.import_module(module_path)
		# Obtención del modelo
		for key in FieldTranslation._modules.keys():
			module = FieldTranslation._modules[key]
			if hasattr(module, self.model):
				self.source_model = getattr(module, self.model)
				self.source_model.meta__verbose_name = self.source_model._meta.verbose_name
				self.source_model.meta__verbose_name_plural = self.source_model._meta.verbose_name_plural
				return self.source_model
		
		raise ValueError("El modelo {0} no existe en ningún módulo".format(self.model))

	def _load_source_object(self):
		"""Carga el objeto fuente"""
		if hasattr(self, "source_obj"):
			self.source_text = getattr(self.source_obj, self.field)
			return self.source_obj

		self._load_source_model()
		self.source_obj = self.source_model.objects.get(id=self.object_id)
		return self.source_obj

	@staticmethod
	def delete_orphan_translations(condition={}):
		"""Elimina las traducciones huérfanas"""
		# TODO: optimizar en una única consulta SQL
		translations = FieldTranslation.objects.all()
		for translation in translations:
			translation._load_source_model()
			condition["id"] = translation.object_id
			if not translation.source_model.objects.filter(**condition).exists():
				self.delete()
	
	
	
	@staticmethod
	def update_translations(condition={}):
		"""
		Actualiza todos los datos de todos los modelos
		"""
		
		import importlib
		import inspect
		import sys
		
		# Número de traducciones actualizadas
		num_translations = 0
		
		# Cacheo de los módulos
		if len(FieldTranslation._modules.keys())==0:
			for module_path in FieldTranslation._model_module_paths:
				FieldTranslation._modules[module_path] = importlib.import_module(module_path)

		# Diccionario con los idiomas
		LANGUAGES = dict(lang for lang in MODELTRANSLATION_LANG_CHOICES)
		if settings.LANGUAGE_CODE in LANGUAGES:
			del LANGUAGES[settings.LANGUAGE_CODE]

		# Obtención de cada modelo
		for key in FieldTranslation._modules.keys():
			module = FieldTranslation._modules[key]

			# Coge todas las clases del módulo
			clsmembers = inspect.getmembers(sys.modules[key], inspect.isclass)
			for cls in clsmembers:
				cls = cls[1]

				# Si tienen cammpos traducibles, le añadimos las traducciones
				if hasattr(cls,"_meta") and not cls._meta.abstract and hasattr(cls._meta,"translatable_fields") and len(cls._meta.translatable_fields)>0:
					objects = cls.objects.filter(**condition)
					
					# Para cada objeto, actualizamos cada idioma y campo
					for obj in objects:
						for lang in LANGUAGES.keys():
							for field in cls._meta.translatable_fields:
								if FieldTranslation.update(obj, field, lang, context=""):
									num_translations += 1
		return num_translations


	def get_source_obj(self):
		"""
		Devuelve el objeto fuente.
		Esto es, el objeto al que está asociada esta traducción.
		"""
		return self._load_source_object()

	def get_source_model(self):
		"""
		Devuelve el modelo fuente.
		Esto es, el modelo cuyo objeto que está asociado a esta traducción.
		"""
		return self._load_source_model()

	def get_verbose_field_name(self):
		self._load_source_model()
		try:
			verbose_field_name = self.source_model._meta.get_field_by_name(self.field)[0].verbose_name
			return verbose_field_name
		except:
			return u"Error cargando el nombre del campo"

	@staticmethod
	def factory(obj, field, source_text, lang, context=""):
		# Obtención del nombre del modelo
		obj_classname = obj.__class__.__name__
		
		# Obtención del MD5 del campo
		#print "Source_text " + source_text
		source_md5 = checksum(source_text)
		#print "Source MD5 " + source_md5
		
		# Obtención del texto traducido
		translation = ""
		field_lang = trans_attr(field,lang)
		#print field_lang
		if hasattr(obj,field_lang) and getattr(obj,field_lang)!="":
			translation = getattr(obj,field_lang)
			#print "Tiene el atributo {0} y su valor es {1}".format(field_lang, translation)
		
		#print "Tiene el atributo {0} y su valor es '{1}'".format(field_lang, translation)

		# Obtención del campo que indica si el campo es fuzzy
		is_fuzzy = True
		is_fuzzy_lang = trans_is_fuzzy_attr(field,lang)
		#print "Atributo "+is_fuzzy_lang
		if hasattr(obj,is_fuzzy_lang):
			is_fuzzy = getattr(obj,is_fuzzy_lang)

		#print "Atributo "+is_fuzzy_lang+" es "+str(is_fuzzy)

		# Llamada a la creación de la traducción del modelo
		trans = FieldTranslation(model=obj_classname, object_id=obj.id, field=field, lang=lang, source_text=source_text, source_md5=source_md5, translation=translation, is_fuzzy=is_fuzzy, context=context)
		return trans


	## Actualiza el contenido del objeto y guarda en base de datos
	def _update(self, obj, field, source_text, context=""):
		#### Actualización 1: Actualización del "is_fuzzy"
		# Obtención del campo que indica si el campo es fuzzy
		lang = self.lang
		is_fuzzy = False
		is_fuzzy_lang = trans_is_fuzzy_attr(field,lang)
		#print "Atributo "+is_fuzzy_lang
		if hasattr(obj,is_fuzzy_lang):
			is_fuzzy = getattr(obj,is_fuzzy_lang)
			#print is_fuzzy_lang+" está en el objeto y su valor es "+str(is_fuzzy)
			self.is_fuzzy = is_fuzzy
		#print is_fuzzy_lang+" = "+str(self.is_fuzzy)
		
		#### Actualización 2: Actualización del objeto completo
		# Obtención del texto y MD5 del campo
		self.source_text = source_text
		self.source_md5 = checksum(source_text)

		# Obtención del texto traducido
		# Puede ser que el mismo objeto tenga el texto traducido
		field_lang = trans_attr(field,lang)
		if hasattr(obj,field_lang):
			translation = getattr(obj,field_lang)
			# Si la traducción ha cambiado, actualizamos el contexto
			if self.translation != translation:
				self.context = context
			# Por supuesto, siempre actualizamos la traducción
			self.translation = translation

		# Obligamos a que si la traducción es vacía, ésta nunca podrá
		# mostrarse al público, por tanto, is_fuzzy=True
		if self.translation == "":
			self.is_fuzzy = True
		
		self.save()
		#print unicode(self)
		#print "Después de guardar "+is_fuzzy_lang+" = "+str(self.is_fuzzy)
		#print "\n"
		return self

	## Actualiza una traducción de forma estática
	@staticmethod
	def update(obj, field, lang, context=""):
		try:
			obj_classname = obj.__class__.__name__
			trans = FieldTranslation.objects.get(model=obj_classname, object_id=obj.id, field=field, lang=lang)
			#print "Traducción "+str(trans)
			return trans._update(obj=obj, field=field, source_text=getattr(obj,field), context=context)
		except FieldTranslation.DoesNotExist:
			trans = FieldTranslation.factory(obj=obj, field=field, source_text=getattr(obj,field), lang=lang, context=context)
			#print "Nueva traducción "+str(trans)
			#trans.save()
			return trans._update(obj=obj, field=field, source_text=getattr(obj,field), context=context)
			return trans

	## Save object in database, updating the datetimes accordingly
	def save(self, *args, **kwargs):
		"""
		Save object in database, updating the datetimes accordingly.
		
		"""
		# Datetime con el momento actual en UTC
		now_datetime = timezone.now()
		# Si no se ha guardado aún, el datetime de creación es la fecha actual
		if not self.id:
			self.creation_datetime = timezone.now()
		# El datetime de actualización es la fecha actual
		self.last_update_datetime = timezone.now()
		
		# El usuario actual es el creador
		# (usamos el middleware django-cuser)
		self.creator_user = None
		current_user = CuserMiddleware.get_user()
		if not current_user is None and not current_user.is_anonymous():
			self.creator_user_id = current_user.id
		
		# Llamada al constructor del padre
		super(FieldTranslation, self).save(*args, **kwargs)


