from SPARQLWrapper import SPARQLWrapper, JSON
from django.utils import timezone
from datetime import timedelta
from .models import DBpediaArtist
import urllib.parse
import urllib.error as urlerror
import socket
import time

DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"
CACHE_TTL_DAYS = 120        # după 4 luni revalidăm artistul
RETRY_COUNT = 3             # cate retry max facem
TIMEOUT = 30                # sec
USER_AGENT = "provenance-app/1.0 (contact: example@example.com)"

def _make_client():
    client = SPARQLWrapper(DBPEDIA_ENDPOINT)
    client.setTimeout(TIMEOUT)
    client.setReturnFormat(JSON)
    client.addCustomHttpHeader("User-Agent", USER_AGENT)
    return client

def _resolve_resource_uri(full_name: str) -> str:

    safe_name = full_name.replace('"', '\"')
    client = _make_client()
    client.setQuery(f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?res WHERE {{
      ?res rdfs:label ?label .
      FILTER (LANG(?label) IN ('en','ro','it','fr','de','es'))
      FILTER (lcase(str(?label)) = lcase("{safe_name}"))
    }}
    LIMIT 1
    """)
    try:
        results = client.query().convert()
        bindings = results.get("results", {}).get("bindings", [])
        if bindings:
            return bindings[0]["res"]["value"]
    except Exception:
        pass
    # Fallback to naive resource URI
    resource_name = urllib.parse.quote(full_name.replace(" ", "_"))
    return f"http://dbpedia.org/resource/{resource_name}"

def get_author_details(full_name: str):

    try:
        artist = DBpediaArtist.objects.get(name=full_name)
        if artist.fetched_at > timezone.now() - timedelta(days=CACHE_TTL_DAYS):
            return _to_dict(artist)
        # dacă e expirat -> revalidăm din DBpedia
    except DBpediaArtist.DoesNotExist:
        artist = None

        resource_uri = _resolve_resource_uri(full_name)

        sparql = _make_client()
        sparql.setQuery(f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?abstract ?birthDate ?birthPlaceLabel ?nationalityLabel ?movementLabel ?thumbnail WHERE {{
      OPTIONAL {{ <{resource_uri}> dbo:abstract ?abstract . FILTER(lang(?abstract)='en') }}
      OPTIONAL {{ <{resource_uri}> dbo:birthDate ?birthDate }}
      OPTIONAL {{ <{resource_uri}> dbo:birthPlace ?birthPlace .
                 ?birthPlace rdfs:label ?birthPlaceLabel . FILTER(lang(?birthPlaceLabel)='en') }}
      OPTIONAL {{ <{resource_uri}> dbo:nationality ?nationality .
                 ?nationality rdfs:label ?nationalityLabel . FILTER(lang(?nationalityLabel)='en') }}
      OPTIONAL {{ <{resource_uri}> dbo:movement ?movement .
                 ?movement rdfs:label ?movementLabel . FILTER(lang(?movementLabel)='en') }}
      OPTIONAL {{ <{resource_uri}> dbo:thumbnail ?thumbnail }}
    }}
    LIMIT 1
    """)

    data = None
    for attempt in range(RETRY_COUNT):
        try:
            results = sparql.query().convert()
            data = _extract_data(results)
            break
        except (socket.timeout, urlerror.HTTPError, urlerror.URLError) as e:
            print(f"[DBPEDIA RETRY {attempt+1}] {full_name} → {e}")
            time.sleep(0.5 * (attempt + 1))
        except Exception as e:
            print(f"[DBPEDIA ERROR] {full_name} → {e}")
            break

    if data is None:
        print(f"[DBPEDIA FAIL] folosesc fallback cache pt {full_name}")
        if artist:
            return _to_dict(artist)
        return _empty()

    db_obj, _ = DBpediaArtist.objects.update_or_create(
        name=full_name,
        defaults=data
    )
    return _to_dict(db_obj)


def _extract_data(results):
    data = _empty()
    if results["results"]["bindings"]:
        b = results["results"]["bindings"][0]
        data["abstract"] = b.get("abstract", {}).get("value")
        data["birthDate"] = b.get("birthDate", {}).get("value")
        data["birthPlace"] = b.get("birthPlaceLabel", {}).get("value")
        data["nationality"] = b.get("nationalityLabel", {}).get("value")
        data["movement"] = b.get("movementLabel", {}).get("value")
        data["image_url"] = b.get("thumbnail", {}).get("value")
    return data

def _to_dict(obj):
    return {
        "abstract": obj.abstract,
        "birthDate": obj.birthDate,
        "birthPlace": obj.birthPlace,
        "nationality": obj.nationality,
        "movement": obj.movement,
        "image_url": obj.image_url
    }

def _empty():
    return {
        "abstract": None,
        "birthDate": None,
        "birthPlace": None,
        "nationality": None,
        "movement": None,
        "image_url": None
    }
