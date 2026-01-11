from django.apps import AppConfig
import os

class ArtworksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'artworks'

    def ready(self):
        if os.environ.get("DJANGO_PRELOAD_DB") == "1":
            from .preload_dbpedia import preload_all
            preload_all(limit=20)
