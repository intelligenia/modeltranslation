# -*- coding: utf-8 -*-

import copy

from django import forms
from django.conf import settings
#from django.utils.translation import ugettext as _

from modeltranslation.models import trans_attr, trans_is_fuzzy_attr


########################################################################
## Useful ModelForm to translatable models
class TranslatableModelForm(forms.ModelForm):

	####################################################################
	## Automatically add new fields for each language you have in your system
	def _add_translation_form_fields(self):
		# Model of the ModelForm
		cls = self._meta.model
		# If Model has no translatable fields
		if not hasattr(cls,"_meta") or not hasattr(cls._meta,"translatable_fields") or len(cls._meta.translatable_fields)==0:
			return False

		# If it is an edition, load the current translations of the object
		if self.instance:
			self.instance.load_translations()

		# For each translatable field a new field for each language is created
		translatable_fields = cls._meta.translatable_fields

		_ = lambda x : x

		for translatable_field in translatable_fields:
			# Add additional language fields only if that field is present
			# in the ModelForm
			if (hasattr(self._meta, "fields") and self._meta.fields and translatable_field in self._meta.fields) or\
				(hasattr(self._meta, "exclude") and self._meta.exclude and not translatable_field in self._meta.exclude):

				self.fields[translatable_field].widget.is_translatable = True
				self.fields[translatable_field].widget.translation_group = translatable_field
				self.fields[translatable_field].widget.lang = settings.LANGUAGE_CODE

				if not settings.IS_MONOLINGUAL:
					for language_pair in settings.LANGUAGES:
						lang = language_pair[0]
						language_name = language_pair[1]

						if lang != settings.LANGUAGE_CODE:
							# Adds a translatable field
							# It is empty by default, its language must not be current language and
							# it should not be required
							field_lang = trans_attr(translatable_field, lang)
							self.fields[field_lang] = copy.deepcopy(self.fields[translatable_field])
							self.fields[field_lang].label += u" ({0})".format(language_name)
							self.fields[field_lang].initial = ""
							self.fields[field_lang].widget.lang = lang
							self.fields[field_lang].required = False

							# Original field label
							field_label = self.fields[translatable_field].label

							# If we are editing a Model instance, sets its correct initial values
							if self.instance and hasattr(self.instance, field_lang):
								self.fields[field_lang].initial = getattr(self.instance, field_lang)

							# is_fuzzy fields
							isfuzzy_lang = trans_is_fuzzy_attr(translatable_field,lang)
							self.fields[isfuzzy_lang] = forms.ChoiceField(
								choices=(
									(u"0",_(u"No necesita revisión")),
									(u"1", _(u"Necesita revisión"))),
								label=_(u"'{0}' necesita revisión para idioma {1}").format(field_label, language_name), initial="1")
							self.fields[isfuzzy_lang].widget.attrs["class"] = "is_fuzzy"
							if self.instance and hasattr(self.instance, isfuzzy_lang):
								if getattr(self.instance, isfuzzy_lang):
									self.fields[isfuzzy_lang].initial = "1"
								else:
									self.fields[isfuzzy_lang].initial = "0"
		return True


	####################################################################################################################
	## By default, adds the translation fields in the form.
	## Please, take note that if you modify the fields, you have to re-call _add_translation_form_fields to take effect
	## in the new fields
	def __init__(self, *args, **kwargs):
		super(TranslatableModelForm, self).__init__(*args, **kwargs)
		# Translations of the Model fields
		self._add_translation_form_fields()


	####################################################################################################################
	## Assigns translation attributes as dynamic attributes for the new instance or existing instance being edited.
	def save(self, commit=True):
		obj = super(TranslatableModelForm, self).save(commit)
		# The instance has all the translated fields introduced as dynamic attributes
		if hasattr(obj._meta, "translatable_fields") and hasattr(obj, "set_translation_fields"):
			# Set translation fields to object
			obj.set_translation_fields(self.cleaned_data)
			if commit:
				obj.save()
		return obj
