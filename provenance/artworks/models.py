from django.db import models

class DBpediaArtist(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    abstract = models.TextField(null=True, blank=True)
    birthDate = models.CharField(max_length=50, null=True, blank=True)
    birthPlace = models.CharField(max_length=255, null=True, blank=True)
    nationality = models.CharField(max_length=255, null=True, blank=True)
    movement = models.CharField(max_length=255, null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Artwork(models.Model):
    title = models.CharField(max_length=255)
    creator = models.CharField(max_length=255, null=True, blank=True)
    date = models.CharField(max_length=50, null=True, blank=True)
    museum = models.CharField(max_length=255, null=True, blank=True)
    movement = models.CharField(max_length=255, null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.title

class GettyULAN(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    ulan_id = models.CharField(max_length=50, null=True, blank=True)
    ulan_url = models.URLField(null=True, blank=True)
    preferred_label = models.CharField(max_length=255, null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.ulan_id})"

class GettyAAT(models.Model):
    term = models.CharField(max_length=255, unique=True, db_index=True)
    aat_id = models.CharField(max_length=50, null=True, blank=True)
    aat_url = models.URLField(null=True, blank=True)
    preferred_label = models.CharField(max_length=255, null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.term} ({self.aat_id})"
