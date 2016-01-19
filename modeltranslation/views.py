# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, render, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404

from django.core.urlresolvers import reverse
from django.db import transaction
from modeltranslation.forms import FieldTranslationForm, ImportTranslationsForm

from modeltranslation.models import checksum, FieldTranslation, trans_attr, trans_is_fuzzy_attr

from django.conf import settings

import re
import hashlib

########################################################################
########################################################################
# Index de administración 
def admin(request):
	return render_to_response('modeltranslation/admin/admin.html',{}, RequestContext(request))


########################################################################
########################################################################
# Ver todas las traducciones
def view_all(request, language, filter=None):
	"""
	Visualización del listado de traducciones.
	Muestra todas las traducciones existentes en el sistema.
	"""

	# Si se ha enviado una búsqueda por POST,
	if request.method == "POST":
		data = request.POST.dict()

		if not data["search"] or data["search"]=="":
			return HttpResponseRedirect(reverse("modeltranslation:view_all_url",args=(data["language"],data["filter"])))

		return HttpResponseRedirect(reverse("modeltranslation:view_all_url",args=(data["language"],data["filter"]))+"?search="+data["search"])

	# Si en cambio, no se ha enviado nada por POST,
	# cogemos todo de la URL
	LANGUAGES = dict(lang for lang in settings.LANGUAGES)
	if language not in LANGUAGES.keys():
		raise Http404(u"El idioma {0} no existe".format(language))
	
	if language == settings.LANGUAGE_CODE:
		raise Http404(u"El idioma {0} es el idioma por defecto".format(language))

	# Filtro para las traducciones
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
	
	# Actualiza las traducciones por si ha habido algún cambio en las
	# estructuras de los modelos referenciados y se tienen campos
	# de modelos que ya no los tienen
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
# Editar una traducción al concreto
def edit(request, translation):
	"""
	Edita una traducción.
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
## Importar traducción en formato .po
@transaction.atomic
def import_translations(request, language):
	"""
	Importa las traducciones a partir de un archivo PO. Ten en cuenta
	que el archivo PO ha de ser generado desde esta aplicación, de forma
	que los comentarios sirvan como id de traducción (lo metemos nosotros
	en la exportación).
	"""
	def _import_po_file(uploadedfile, lang):
		lines = []
		for line in uploadedfile:
			lines.append(line)
		num_lines = len(lines)
		
		prog_ctxt = re.compile(r"msgctxt\s+\"(?P<id>\d+)--(?P<model>\w+)--(?P<object_id>\d+)--(?P<field>\w+)\"")
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
					
				# Obtención de la traducción a partir del id
				try:
					field_trans = FieldTranslation.objects.get(id=id)
				except FieldTranslation.DoesNotExist:
					source_text = source_text.replace("msgid","")[1:-1].replace("\\\"","\"").replace('\\\'','\'')
					source_md5 = hashlib.md5(source_text.encode("utf-8")).hexdigest()
					field_trans = FieldTranslation(model=result.group("model"), object_id=result.group("object_id"), field=result.group("field"), lang=lang, source_text=source_text, source_md5=source_md5)
					
				# Establecemos la traducción y si es fuzzy
				field_trans.translation = translation
				field_trans.is_fuzzy = is_fuzzy
				field_trans.save()
				#print translation
				#print is_fuzzy
				i += 4
			i += 1
	
	# Elimina traducciones que no estén asociadas a ningún objeto
	FieldTranslation.delete_orphan_translations()
	
	# Acceso obligatoriamente por POST
	if request.method != "POST":
		return HttpResponseRedirect(reverse("modeltranslation:admin_url"))
	
	form = ImportTranslationsForm(request.POST, request.FILES)
	if form.is_valid():
		_import_po_file(request.FILES['file'], language)
		#cache = TransCache.factory()
		#cache.clear()
		return HttpResponseRedirect(reverse("modeltranslation:view_all_url",args=(language,"all")))

	return HttpResponseRedirect(reverse("modeltranslation:admin_url"))


########################################################################
########################################################################
## Exportar traducción en formato .po
def export_translations(request, language):
	"""
	Vista de exportación de las traducciones
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
## Actualizar las traducciones
def update_translations(request):
	"""
	Actualiza las traducciones eliminando las huérfanas y
	generando traducciones vacías para todos los objetos que existan en
	base de datos.
	"""
	FieldTranslation.delete_orphan_translations()
	num_translations = FieldTranslation.update_translations()
	return render_to_response('modeltranslation/admin/update_translations_ok.html',{"num_translations":num_translations}, RequestContext(request))
	
