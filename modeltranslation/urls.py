# -*- coding: utf-8 -*-

from django.conf.urls import url
from modeltranslation import views

# De esta forma (definiendo un objeto que devuelve los patrones de las URLs
# se pueden definir espacios de nombres "namespaces". Esto viene fatal
# (¡FATAL!) explicado en la documentación ya que viene de pasada.
# La idea es hacer la aplicación de banners portable e independiente
# del proyecto para poder reutilizarla, al estilo de la de administración
# que trae django y al estilo de la aplicación de banners de IntelliWeb
# Me ha costado sudor y sangre conseguir echar a andar esto.

class ModelTranslationUrls(object):
	def __init__(self, name='modeltranslation', app_name='modeltranslation'):
		self.app_name = app_name #Namespace de la aplicación
		self.name = name #Namespace de la instancia

	urlpatterns = [
		url(r'^$', views.admin, name="admin_url"),
		url(r'^(?P<language>[-\w]+)/(?P<filter>(all|completed|fuzzy)*)$', views.view_all, name="view_all_url"), #Para la gestión de las traducciones
		url(r'^edit_translation/(?P<translation>.*)$', views.edit, name="edit_url"), #Para la gestión de las traducciones
		url(r'^import/(?P<language>[-\w]+)$', views.import_translations, name="import_translations_url"), #Importar traducciones
		url(r'^export/(?P<language>[-\w]+)$', views.export_translations, name="export_translations_url"), #Exportar traducciones
		url(r'^update_translations$', views.update_translations, name="update_translations_url"), #Actualizar traducciones
	]

	@property
	def urls(self):
		return (self.urlpatterns, self.app_name, self.name)
