from SPARQLWrapper import SPARQLWrapper, JSON
from django.utils import timezone
from datetime import timedelta
from .models import GettyULAN, GettyAAT
import urllib.error as urlerror
import urllib.parse
import socket
import time
import requests
import json

GETTY_SPARQL_ENDPOINT = "http://vocab.getty.edu/sparql"
GETTY_SPARQL_JSON = "http://vocab.getty.edu/sparql.json"
CACHE_TTL_DAYS = 180 
RETRY_COUNT = 3
TIMEOUT = 30
USER_AGENT = "provenance-app/1.0 (contact: example@example.com)"

def _query_getty_sparql(query: str):
    """Query Getty SPARQL endpoint using POST request"""
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/sparql-results+json',
        'Content-Type': 'application/sparql-query; charset=utf-8'
    }
    
    try:
        response = requests.post(
            GETTY_SPARQL_ENDPOINT,
            data=query.encode('utf-8'),
            headers=headers,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        # Check if response has content
        if not response.text or len(response.text.strip()) == 0:
            print(f"[GETTY SPARQL ERROR] Empty response from Getty endpoint")
            return None
            
        return response.json()
    except requests.exceptions.Timeout:
        print(f"[GETTY SPARQL TIMEOUT] Query timed out after {TIMEOUT}s")
        return None
    except requests.exceptions.JSONDecodeError as e:
        print(f"[GETTY SPARQL ERROR] Invalid JSON response: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[GETTY SPARQL ERROR] Request failed: {e}")
        return None

def search_ulan_sparql(artist_name: str):
    """
    Search Getty ULAN for an artist by name.
    Returns dict with ulan_id, ulan_url, preferred_label or None if not found.
    """
    if not artist_name or artist_name.strip() == "":
        return None
    
    print(f"[GETTY ULAN] Searching for artist: {artist_name}")
    
    # Check cache first
    try:
        cached = GettyULAN.objects.get(name=artist_name)
        if cached.fetched_at > timezone.now() - timedelta(days=CACHE_TTL_DAYS):
            if cached.ulan_id:
                return {
                    "ulan_id": cached.ulan_id,
                    "ulan_url": cached.ulan_url,
                    "preferred_label": cached.preferred_label
                }
            else:
                return None  # Previously searched but not found
    except GettyULAN.DoesNotExist:
        pass
    
    search_names = [artist_name]
    
    if ',' not in artist_name:
        parts = artist_name.strip().split()
        if len(parts) >= 2:
            # For "Pablo Picasso" -> "Picasso, Pablo"
            reversed_name = f"{parts[-1]}, {' '.join(parts[:-1])}"
            search_names.append(reversed_name)
            print(f"[GETTY ULAN] Will also try reversed format: {reversed_name}")
    
    # Try each name variant
    for name_variant in search_names:
        print(f"[GETTY ULAN] Querying Getty with: {name_variant}")
        safe_name = name_variant.replace('\\', '\\\\').replace('"', '\\"')
        
        # Use FILTER with regex (compact format)
        query = f"""PREFIX gvp: <http://vocab.getty.edu/ontology#>
PREFIX xl: <http://www.w3.org/2008/05/skos-xl#>
SELECT ?subject ?label WHERE {{
  ?subject a gvp:PersonConcept ;
           gvp:prefLabelGVP [xl:literalForm ?label] .
  FILTER(regex(?label, "{safe_name}", "i"))
}}
LIMIT 5"""
        
        for attempt in range(RETRY_COUNT):
            try:
                results = _query_getty_sparql(query)
                
                if results:
                    bindings = results.get("results", {}).get("bindings", [])
                    
                    if bindings:
                        subject_uri = bindings[0]["subject"]["value"]
                        label = bindings[0].get("label", {}).get("value", artist_name)
                        
                        ulan_id = subject_uri.split("/")[-1]
                        ulan_url = f"http://vocab.getty.edu/page/ulan/{ulan_id}"
                        
                        GettyULAN.objects.update_or_create(
                            name=artist_name,
                            defaults={
                                "ulan_id": ulan_id,
                                "ulan_url": ulan_url,
                                "preferred_label": label,
                                "fetched_at": timezone.now()
                            }
                        )
                        
                        print(f"[GETTY ULAN] {artist_name} -> {ulan_id} (searched as: {name_variant})")
                        return {
                            "ulan_id": ulan_id,
                            "ulan_url": ulan_url,
                            "preferred_label": label
                        }
                
                
            except Exception as e:
                print(f"[GETTY ULAN RETRY {attempt+1}] {name_variant} → {e}")
                time.sleep(0.5 * (attempt + 1))
                continue 
            
            break
    
    GettyULAN.objects.update_or_create(
        name=artist_name,
        defaults={
            "ulan_id": None,
            "ulan_url": None,
            "preferred_label": None,
            "fetched_at": timezone.now()
        }
    )
    return None

def search_aat_sparql(movement_term: str):
    """
    Search Getty AAT for an art movement/style term.
    Returns dict with aat_id, aat_url, preferred_label or None if not found.
    """
    if not movement_term or movement_term.strip() == "":
        return None
    
    print(f"[GETTY AAT] Searching for movement: {movement_term}")
    
    try:
        cached = GettyAAT.objects.get(term=movement_term)
        if cached.fetched_at > timezone.now() - timedelta(days=CACHE_TTL_DAYS):
            if cached.aat_id:
                return {
                    "aat_id": cached.aat_id,
                    "aat_url": cached.aat_url,
                    "preferred_label": cached.preferred_label
                }
            else:
                return None  
    except GettyAAT.DoesNotExist:
        pass
    
    print(f"[GETTY AAT] Querying Getty with: {movement_term}")
    safe_term = movement_term.replace('\\', '\\\\').replace('"', '\\"')
    
    query = f"""PREFIX gvp: <http://vocab.getty.edu/ontology#>
PREFIX xl: <http://www.w3.org/2008/05/skos-xl#>
SELECT ?subject ?label WHERE {{
  ?subject a gvp:Concept ;
           gvp:prefLabelGVP [xl:literalForm ?label] .
  FILTER(regex(?label, "{safe_term}", "i"))
}}
LIMIT 5"""
    
    for attempt in range(RETRY_COUNT):
        try:
            results = _query_getty_sparql(query)
            
            if results:
                bindings = results.get("results", {}).get("bindings", [])
                
                if bindings:
                    subject_uri = bindings[0]["subject"]["value"]
                    label = bindings[0].get("label", {}).get("value", movement_term)
                    
                    aat_id = subject_uri.split("/")[-1]
                    aat_url = f"http://vocab.getty.edu/page/aat/{aat_id}"
                    
                    GettyAAT.objects.update_or_create(
                        term=movement_term,
                        defaults={
                            "aat_id": aat_id,
                            "aat_url": aat_url,
                            "preferred_label": label,
                            "fetched_at": timezone.now()
                        }
                    )
                    
                    print(f"[GETTY AAT] {movement_term} -> {aat_id}")
                    return {
                        "aat_id": aat_id,
                        "aat_url": aat_url,
                        "preferred_label": label
                    }
            
            GettyAAT.objects.update_or_create(
                term=movement_term,
                defaults={
                    "aat_id": None,
                    "aat_url": None,
                    "preferred_label": None,
                    "fetched_at": timezone.now()
                }
            )
            return None
                
        except Exception as e:
            print(f"[GETTY AAT RETRY {attempt+1}] {movement_term} → {e}")
            time.sleep(0.5 * (attempt + 1))
    
    GettyAAT.objects.update_or_create(
        term=movement_term,
        defaults={
            "aat_id": None,
            "aat_url": None,
            "preferred_label": None,
            "fetched_at": timezone.now()
        }
    )
    return None

def get_getty_enrichment(name_or_term: str, vocabulary: str):
    if vocabulary.lower() == "ulan":
        return search_ulan_sparql(name_or_term)
    elif vocabulary.lower() == "aat":
        return search_aat_sparql(name_or_term)
    else:
        print(f"[GETTY ERROR] Unknown vocabulary: {vocabulary}")
        return None
