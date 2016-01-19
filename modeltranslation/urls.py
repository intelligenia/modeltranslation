# -*- coding: utf-8 -*-

from django.conf.urls import url

# ModelTranslationURLs
from modeltranslation.admin import views


class ModelTranslationUrls(object):
	def __init__(self, name='modeltranslation', app_name='modeltranslation'):
		self.app_name = app_name # App Namespace
		self.name = name # Instance Namespace

	urlpatterns = [
		url(r'^$', views.admin, name="admin_url"),
		url(r'^(?P<language>[-\w]+)/(?P<filter>(all|completed|fuzzy)*)$', views.view_all, name="view_all_url"), # Translation management
		url(r'^edit_translation/(?P<translation>.*)$', views.edit, name="edit_url"), # Edition
		url(r'^import/(?P<language>[-\w]+)$', views.import_translations, name="import_translations_url"), # Translation import
		url(r'^export/(?P<language>[-\w]+)$', views.export_translations, name="export_translations_url"), # Translation export
		url(r'^update_translations$', views.update_translations, name="update_translations_url"), # Update translations
	]

	@property
	def urls(self):
		return (self.urlpatterns, self.app_name, self.name)
