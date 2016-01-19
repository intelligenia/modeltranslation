# -*- coding: utf-8 -*-

import hashlib

from django.shortcuts import render_to_response, render, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.db import transaction
from django.conf import settings
import re

from modeltranslation.admin.forms import FieldTranslationForm, ImportTranslationsForm
from modeltranslation.models import FieldTranslation


########################################################################
########################################################################
# Admin index
def admin(request):
	return render_to_response('modeltranslation/admin/admin.html',{}, RequestContext(request))


########################################################################
########################################################################
# Ver todas las traducciones
def view_all(request, language, filter=None):
	"""
	View all translations that are in site.
	"""

	# Is there any filter?
	if request.method == "POST":
		data = request.POST.dict()

		if not data["search"] or data["search"]=="":
			return HttpResponseRedirect(reverse("modeltranslation:view_all_url",args=(data["language"],data["filter"])))

		return HttpResponseRedirect(reverse("modeltranslation:view_all_url",args=(data["language"],data["filter"]))+"?search="+data["search"])

	LANGUAGES = dict(lang for lang in settings.LANGUAGES)
	if language not in LANGUAGES.keys():
		raise Http404(u"Language {0} does not exist".format(language))
	
	if language == settings.LANGUAGE_CODE:
		raise Http404(u"El idioma {0} es el idioma por defecto".format(language))

	# Translation filter
	trans_filter = {"lang":language}
	if filter == "all" or filter is None:
		pass
	elif filter == "fuzzy":
		trans_filter["is_fuzzy"] = True
	elif filter == "completed":
		trans_filter["is_fuzzy"] = False
	
	search_query = ""
	if request.GET and "search" in request.GET and request.GET.get("search")!="":
		search_query = request.GET.get("search")
		trans_filter["source_text__icontains"] = search_query

	translations = FieldTranslation.objects.filter(**trans_filter)
	
	# Update translations
	active_translations = []
	for translation in translations:
		source_model = translation.get_source_model()
		if not translation.field in source_model._meta.translatable_fields:
			translation.delete()
		else:
			active_translations.append(translation)
	
	replacements = {"translations":active_translations, "filter":filter, "lang":language, "language":LANGUAGES[language], "search_query":search_query}
	return render_to_response('modeltranslation/admin/list.html',replacements, RequestContext(request))


########################################################################
########################################################################
# Edit a translation
def edit(request, translation):
	"""
	Edit a translation.
	@param request: Django HttpRequest object.
	@param translation: Translation id
	@return Django HttpResponse object with the view or a redirection.
	"""
	translation = get_object_or_404(FieldTranslation, id=translation)
	if request.method == 'POST':
		if "cancel" in request.POST:
			return HttpResponseRedirect(reverse("modeltranslation:view_all_url",args=(translation.lang,"all")))
		elif "save" in request.POST:
			form = FieldTranslationForm(request.POST, instance=translation)
			valid_form = form.is_valid()
			if valid_form:
				translation = form.save(commit=False)
				translation.context = u"Admin. Traducciones"
				translation.save()
				return HttpResponseRedirect(reverse("modeltranslation:view_all_url",args=(translation.lang,"all")))
		else:
			form = FieldTranslationForm(instance=translation)
	else:
		form = FieldTranslationForm(instance=translation)

	LANGUAGES = dict(lang for lang in settings.LANGUAGES)
	language = LANGUAGES[translation.lang]
	
	return render_to_response('modeltranslation/admin/edit_translation.html',{"translation":translation, "form":form, "lang":translation.lang, "language":language}, RequestContext(request))


########################################################################
########################################################################
## Import translation in .po format
@transaction.atomic
def import_translations(request, language):
	"""
	Import translations froma PO file. Please take note that this PO file MUST be generated with this application
	because translation comments in the file are used as translation ids.
	"""
	def _import_po_file(uploadedfile, lang):
		lines = []
		for line in uploadedfile:
			lines.append(line)
		num_lines = len(lines)
		
		prog_ctxt = re.compile(r"msgctxt\s+\"(?P<id>\d+)--(?P<module>(\.\w)+)--(?P<model>\w+)--(?P<object_id>\d+)--(?P<field>\w+)\"")
		prog_msgid = re.compile(r"msgid\s+\"(?P<source_text>.+)\"$")
		prog_msgstr = re.compile(r"msgstr\s+(?P<trans>.+)")
		
		i = 0
		while i < num_lines:
			line = lines[i]
			result = prog_ctxt.match(line)
			if result:
				id = result.group("id")
				is_fuzzy = (lines[i-1] == "#, fuzzy\n")

				source_text = lines[i+1]
				translation_line = lines[i+2]

				# Traducción
				g = prog_msgstr.match(translation_line)
				if g is None:
					i += 1
					continue
				translation = g.group("trans").replace("msgstr","")[1:-1].replace("\\\"","\"").replace('\\\'','\'')
					
				# Get translation from a translation id
				try:
					field_trans = FieldTranslation.objects.get(id=id)
				except FieldTranslation.DoesNotExist:
					source_text = source_text.replace("msgid","")[1:-1].replace("\\\"","\"").replace('\\\'','\'')
					source_md5 = hashlib.md5(source_text.encode("utf-8")).hexdigest()
					field_trans = FieldTranslation(
						module=result.group("module"), model=result.group("model"), object_id=result.group("object_id"),
						field=result.group("field"), lang=lang, source_text=source_text, source_md5=source_md5
					)
					
				# Sets translation and is_fuzzy attribute
				field_trans.translation = translation
				field_trans.is_fuzzy = is_fuzzy
				field_trans.save()
				i += 4
			i += 1
	
	# Delete orphan translations
	FieldTranslation.delete_orphan_translations()
	
	if request.method != "POST":
		return HttpResponseRedirect(reverse("modeltranslation:admin_url"))
	
	form = ImportTranslationsForm(request.POST, request.FILES)
	if form.is_valid():
		_import_po_file(request.FILES['file'], language)
		return HttpResponseRedirect(reverse("modeltranslation:view_all_url",args=(language,"all")))

	return HttpResponseRedirect(reverse("modeltranslation:admin_url"))


########################################################################
########################################################################
## Export translation in PO format
def export_translations(request, language):
	"""
	Export translations view.
	"""
	FieldTranslation.delete_orphan_translations()
	translations = FieldTranslation.objects.filter(lang=language)
	for trans in translations:
		trans.source_text = trans.source_text.replace("'","\'").replace("\"","\\\"")
		trans.translation = trans.translation.replace("'","\'").replace("\"","\\\"")
	replacements = {"translations":translations, "lang":language}
	if len(settings.ADMINS)>0:
		replacements["last_translator"] = settings.ADMINS[0][0]
		replacements["last_translator_email"] = settings.ADMINS[0][1]
	if settings.WEBSITE_NAME:
		replacements["website_name"] = settings.WEBSITE_NAME
	response = render(request=request, template_name='modeltranslation/admin/export_translations.po', dictionary=replacements, context_instance=RequestContext(request), content_type="text/x-gettext-translation")
	response['Content-Disposition'] = 'attachment; filename="{0}.po"'.format(language)
	return response


########################################################################
########################################################################
## Update translations
def update_translations(request):
	"""
	Update translations: delete orphan translations and creates empty translations for new objects in database.
	"""
	FieldTranslation.delete_orphan_translations()
	num_translations = FieldTranslation.update_translations()
	return render_to_response('modeltranslation/admin/update_translations_ok.html',{"num_translations":num_translations}, RequestContext(request))
	
