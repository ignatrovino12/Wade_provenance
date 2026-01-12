from django.urls import path
from . import views

urlpatterns = [
    path('', views.artworks_page, name="artworks_page"),
    path('api/', views.artworks_api, name="artworks_api"),
    path('sparql', views.sparql_endpoint, name="sparql_endpoint"),
    path('stats/', views.statistics_page, name="statistics_page"),
    path('stats/api/', views.statistics_api, name="statistics_api"),
    path('getty/stats/', views.getty_statistics_page, name="getty_statistics_page"),
    path('getty/stats/api/', views.getty_statistics_api, name="getty_statistics_api"),
    path('romanian/', views.romanian_heritage_page, name="romanian_heritage_page"),
    path('romanian/api/', views.romanian_heritage_api, name="romanian_heritage_api"),
]
