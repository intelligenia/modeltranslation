# modeltranslation

Versión en español en [README.es.md](README.es.md)

## Introduction

This application allows you use [Django](https://www.djangoproject.com/) model translations easily. Everything is based on FieldTranslation,
a class that stores the translation of each field of your application models.

All the process is transparent and the entries are created when save is called.

You will not have to modify FieldTranslation, but you can read the code.

All code in in the github repository: [https://github.com/intelligenia/modeltranslation](https://github.com/intelligenia/modeltranslation)

## Instructions

### Installation

This application depends on [django-cuser](https://pypi.python.org/pypi/django-cuser) and [TinyMCE](https://pypi.python.org/pypi/django-tinymce),
so you will need to install it and put it in the list of INSTALLED_APPS before modeltranslation.

You are encouraged to use pip to install django-cuser.

The easiest way to install modeltranslation is by installing it from [pipy](https://pypi.python.org/pypi/modeltranslation):

```sh
pip install modeltranslation
```

Once you've done this, you can install modeltranslation in settings.py:

INSTALLED_APPS = (
  "tinymce",
  "cuser",
  "modeltranslation"
)

## Add IS_MONOLINGUAL to settings.py

You'll have to include a new setting in settings.py IS_MONOLINGUAL=False. IS_MONOLINGUAL acts as a switch for modeltranslation:

```python
# modeltranslation only works when IS_MONOLINGUAL is False
IS_MONOLINGUAL=False
```

### Add TRANSLATABLE_MODEL_MODULES to settings.py

Add file setting TRANSLATABLE_MODEL_MODULES to settings.py. TRANSLATABLE_MODEL_MODULES contains a list of module paths that will be translated. For example:
	
```python
TRANSLATABLE_MODEL_MODULES = ["app1.models", "app2.models", "fees.models", "menus.models", ...]
```

## Import addtranslations

Import **addtranslations** if each of your models.py files:

```python
from modeltranslation.translation import addtranslations
```

After that, you'll have to call **addtranslations** at the end of this file:

```python
addtranslations(__name__)
```

This call adds an observer that saves translations when **save** model method is executed.

## Add translatable_fields to your models

Modify your models including a meta field "translatable_fields". This field is a list with the fields you want to translate.

For example:

```python
from django.db import models

class Event(models.Model):
	
	name = models.CharField(blank=False, max_length=150, verbose_name=u"Name", help_text=u"Name of the event.")
	description = models.TextField(blank=False, verbose_name=u"Description", help_text=u"Long description of the event.")
	short_description = models.CharField(blank=False, max_length=150, verbose_name=u"Short description", help_text=u"Short description of the event.")

	#...

	## Event Meta
	class Meta:
		verbose_name = "event"
		verbose_name_plural = "events"
		translatable_fields = ("name", "description", "short_description")

```

### And that's all!

Now you have everything configurated and can use modeltranslation translations.


## How to use translations in ModelForms

Make your ModelForm object inherits of TranslatableModelForm. This will
include automatically the extra fields for each language you have in
your website.

```python
from modeltranslation.forms import TranslatableModelForm

class EventForm(TranslatableModelForm):
	pass
```

If you need to modify any of the fields in __init__ method (for example
by changing the widget of one field), you'll have to call
_add_translation_form_fields after your changes.

For example:

```python
	# EventForm __init__ 
	def __init__(self, event, *args, **kwargs):
		super(EventForm, self).__init__(*args, **kwargs)
		
		# Adds TinyMCE editor but we also want this editor in other
		# languages' description fields
		self.fields["description"].widget = TinyMCE()
		
		# Manually adition of translation fields
		self._add_translation_form_fields()
```

## Dynamic translations in Django templates

1. Include modeltranslation filters in each template you wan to use this special filters.

```django
{% load modeltranslation_tags %}
```

2. Use filter "_" with the object and one of its fields. This filter will
return the translation of that field in the current language.

For example: 

```django
{{ event|_:"name" }} {# Translates event name #}
{{ event.area|_:"name" }} {# Translates area name #}
```

## Dynamic translations in code

This application injects a new method to each translatable model: **get_trans_attr**.
This method returns the translation of the attribute in the current language (if it exists),
otherwise returns the default value for this attribute:

For example: 
```python

# Original event name
original_event_name event.name

# Translated event name
translated_event_name event.get_trans_attr("name")
```

## Contact and suggestions

- Create a new issue in this repository.
- Email me at diegoREMOVE_THIS@intelligeniaREMOVE_THIS.com

