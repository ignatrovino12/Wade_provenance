from django.db import models

class DBpediaArtist(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    abstract = models.TextField(null=True, blank=True)
    birthDate = models.CharField(max_length=50, null=True, blank=True)
    birthPlace = models.CharField(max_length=255, null=True, blank=True)
    nationality = models.CharField(max_length=255, null=True, blank=True)
    movement = models.CharField(max_length=255, null=True, blank=True)
    
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Artwork(models.Model):
    title = models.CharField(max_length=255)
    creator = models.CharField(max_length=255, null=True, blank=True)
    date = models.CharField(max_length=50, null=True, blank=True)
    museum = models.CharField(max_length=255, null=True, blank=True)
    movement = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title
