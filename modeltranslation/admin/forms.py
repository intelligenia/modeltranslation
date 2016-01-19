# -*- coding: utf-8 -*-

########################################################################
##
## Formularios para la traducción masiva de textos
##
########################################################################

from django import forms

from modeltranslation.models import FieldTranslation

from tinymce.widgets import TinyMCE

import re

def has_html_tag(text):
	result = re.match(r"<p>|<ul>|<img>|<strong>|<span>", text)
	return result


class ModelFormTrimForm(forms.ModelForm):

	def clean(self):
		cleaned_data = super(ModelFormTrimForm, self).clean()

		for field in self.cleaned_data:
			if isinstance(self.cleaned_data[field], basestring):
				self.cleaned_data[field] = self.cleaned_data[field].strip()

		#Hay que devolver siempre el array "cleaned_data"
		return cleaned_data


class FieldTranslationForm(ModelFormTrimForm):
	class Meta:
		model = FieldTranslation
		exclude = ("module", "model", "object_id", "field", "lang", "source_text", "source_md5", "context", "creation_datetime", "last_update_datetime", "creator_user")

	class Media:
		css = {
			"all": ("css/modeltranslation/forms/common.css",)
		}

		js = (
			"js/modeltranslation/forms/common.js",
		)

	def __init__(self, *args, **kwargs):
		super(FieldTranslationForm, self).__init__(*args, **kwargs)
		if self.instance and has_html_tag(self.instance.source_text):
			self.fields["translation"].widget = TinyMCE()

	def clean(self):
		cleaned_data = super(FieldTranslationForm, self).clean()
		return cleaned_data
		
	def save(self, *args, **kwargs):
		obj = super(FieldTranslationForm, self).save(*args, **kwargs)
		return obj


########################################################################
########################################################################
## Actualizador del archivo .po
class ImportTranslationsForm(forms.Form):
	file = forms.FileField()
