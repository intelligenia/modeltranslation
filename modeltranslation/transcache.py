# -*- coding: utf-8 -*-

########################################################################################################################
########################################################################################################################
#### THIS IS NOT USED. FUTURE VERSIONS WILL IMPROVE PERFORMANCE BY USE OF THIS CACHE OF TRANSLATIONS
########################################################################################################################
########################################################################################################################


###########################################
# Lo básico sobre los modelos
from django.db import models
from django.utils import timezone

## Clase singleton que tiene 
class TransCache:
    
    ## Diccionario que contiene la caché
    cache = {}
    
    ## Fecha de creación de la caché
    SINGLETON_CREATION_DATETIME = None
    
    ## Tiempo de vida de la caché
    SINGLETON_EXPIRATION_MAX_SECONDS = 7200
    
    ## Tamaño de la caché
    SINGLETON_SIZE = 1000
    
    ## Tamaño de la caché
    SINGLETON = None
    
    @staticmethod
    def _create_key(lang, instance):
        """Crea la clave única de la caché"""
        model_name = instance.__class__.__name__
        return "{0}__{1}_{2}".format(lang,model_name,instance.id)

    @staticmethod
    def _cache_is_expired():
        """Indica si la caché está caducada"""
        now = timezone.now()
        timediff = TransCache.SINGLETON_CREATION_DATETIME - now
        return (timediff.total_seconds() > TransCache.SINGLETON_EXPIRATION_MAX_SECONDS)
    
    def _cache_is_too_big(self):
        """Indica si la caché es demasiado grande"""
        return len(self.cache) > TransCache.SINGLETON_SIZE
    
    def __init__(self, *args, **kwargs):
        """Inicializa la caché de traducciones"""
        self.cache = {}
    
    @staticmethod
    def factory():
        """Factoría del singleton, o crea una nueva o devuelve la existente"""
        if not TransCache.SINGLETON or TransCache._cache_is_expired():
            TransCache.SINGLETON = TransCache()
            TransCache.SINGLETON_CREATION_DATETIME = timezone.now()

        return TransCache.SINGLETON

    def clear(self):
        """Limpia la caché"""
        self.cache = {}
        self.creation_datetime = timezone.now()

    def set(self, lang, instance):
        """
        Establece en la instancia actual los atributos de traducción
        y la almacena en un diccionario de claves _create_key y valores
        el objeto con los atributos dinámicos.
        """
        if self._cache_is_too_big():
            self.cache = {}
        instance_key = TransCache._create_key(lang, instance)
        instance._translations_are_cached = True
        instance.load_translations(lang=lang)
        self.cache[instance_key] = instance
        
    def has(self, lang, instance):
        """
        Indica si la caché tiene un objeto igual a éste con los
        atributos dinámicos de traducción
        """
        instance_key = TransCache._create_key(lang, instance)
        return instance_key in self.cache

    def get(self, lang, instance):
        """
        Obtiene una instancia igual a ésta, pero con los atributos
        dinámicos de traduccción
        """
        instance_key = TransCache._create_key(lang, instance)
        return self.cache[instance_key]

