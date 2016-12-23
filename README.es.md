# modeltranslation

English version in [README.md](README.md).

## Introducción

Esta aplicación de [Django](https://www.djangoproject.com/) permite realizar traducciones
de los campos de los modelos y las almacena en una tabla de la BD.
De esta forma, cada vez que se ejecute el método save() se genera una entrada incompleta en una tabla. Luego el
traductor podrá traducir esas entradas incompletas.

Tú no deberías tocar el modelo FieldTranslation, pero si lo deseas puedes leer el código.

Todo el código está en el siguiente repositori de github: [https://github.com/intelligenia/modeltranslation](https://github.com/intelligenia/modeltranslation)

## Instrucciones para usar la aplicación

### Instalación.

Esta aplicación depende de [django-cuser](https://pypi.python.org/pypi/django-cuser), y de [TinyMCE](https://pypi.python.org/pypi/django-tinymce)
por lo que deberás instalarlo antes y ponerlo encima en el listado de aplicaciones instaladas.

Puedes usar pip para instalar django-cuser.

Ahora sí, para instalar la aplicación modeltranslation en settings.py debes
incluirla en el listado de aplicaciones instaladas.

INSTALLED_APPS = (
  "tinymce",
  "cuser",
  "modeltranslation"
)

###	Añadir IS_MONOLINGUAL

Usar la opción IS_MONOLINGUAL=False en settings.py para indicar que el sitio tiene varios idiomas:

```python
IS_MONOLINGUAL=False
```

### Añadir TRANSLATABLE_MODEL_MODULES

Añadir en el fichero settings.py un TRANSLATABLE_MODEL_MODULES con una lista de las rutas de los modelos que van a ser traducidas. Por ejemplo:
	
```python
TRANSLATABLE_MODEL_MODULES = ["app1.models", "app2.models", "fees.models", "menus.models", ...]
```

### Importar addtranslations en los modelos

Importar addtranslations en el fichero de modelos de tu aplicación:

```python
from modeltranslation.translation import addtranslations
```

Luego, tendrás que realiza esta llamada al FINAL de ese mismo fichero de modelos:

```python
addtranslations(__name__)
```

Esta llamada lo que hace es añadir un observador que se encarga de guardar
las traducciones cuando se ejecuta el método **save** del modelo.

## Añadir translatable_fields a los modelos

Modifica los modelos de tu aplicación incluyendo un campo "translatable_fields" en el Meta con una lista de los atributos a traducir.

Por ejemplo:

```python
from django.db import models

class Event(models.Model):

	name = models.CharField(blank=False, max_length=150, verbose_name=u"Nombre", help_text=u"Nombre del evento.")
	description = models.TextField(blank=False, verbose_name=u"Descripción", help_text=u"Descripción larga del evento.")
	short_description = models.CharField(blank=False, max_length=150, verbose_name=u"Descripción corta", help_text=u"Texto (máximo 150 caracteres) que sirve como descripción breve del evento.")

	#...

	## Metainformación sobre Event
	class Meta:
		verbose_name = "evento"
		verbose_name_plural = "eventos"
		translatable_fields = ("name", "description", "short_description")

```
### FIN

A partir de este momento, tienes la aplicación de gestión de traducciones


## Uso de traducciones en los formularios de modelos

Hereda de TranslatableModelForm en tu formulario. Esto hará que se incluyan
un campo extra por cada campo e idioma y será el encargado de guardar los
datos una vez que se guarde el objeto.

```python
from modeltranslation.forms import TranslatableModelForm

class EventForm(TranslatableModelForm):
	pass
```

Si quieres modificar alguno de los campos en el método __init__ del
formulario, tendrás que volver a llamar al método de TranslatableModelForm
encargado de crear los nuevos campos. Por ejemplo:

```python
	# Método __init__ del formulario EventForm
	def __init__(self, event, *args, **kwargs):
		super(EventForm, self).__init__(*args, **kwargs)
		
		# Inclusión del editor TinyMCE, queremos que se muestre el editor
		# en los campos extra generados por el sistema de traducciones
		self.fields["description"].widget = TinyMCE()
		
		# Por lo que hemos de añadir las traducciones a mano
		self._add_translation_form_fields()
```

## Traducciones dinámicas en las plantilla de Django

1. Incluir los filtros en cada plantilla que use traducciones. Nótese
que se ha de incluir en TODAS las que usen los nuevos filtros, olvídate
de la herencia.

```django
{% load modeltranslation_tags %}
```

2. Usar el filtro "_" (sí, se llama guionbajo) sobre el objeto con
atributos traducibles pasándole como parámetro el atributo a traducir.

Por ejemplo: 

```django
{{ event|_:"name" }} {# Traduce el nombre del evento #}
{{ event.area|_:"name" }} {# Traduce el nombre del área #}
```

## Traducciones dinámicas en el código

Para obtener automáticamente un atributo traducido, puedes hacer uso
del método **get_trans_attr** inyectados en los modelos traducibles:

Por ejemplo: 
```python

# Nombre del evento en el idioma por defecto
original_event_name event.name

# Nombre del evento traducido
translated_event_name event.get_trans_attr("name")
```

## Contacto, dudas y sugerencias

- Crea una incidencia en el respositorio.
- Escribe al autor en diegoREMOVE_THIS@intelligeniaREMOVE_THIS.com

