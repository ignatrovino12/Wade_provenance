"""
Getty Vocabularies Integration (AAT, ULAN, TGN)
- AAT (Art & Architecture Thesaurus) for movements, styles, techniques
- ULAN (Union List of Artist Names) for artists
- TGN (Thesaurus of Geographic Names) for places
"""

import requests
from SPARQLWrapper import SPARQLWrapper, JSON
import xml.etree.ElementTree as ET
import time

# Getty SPARQL endpoint
GETTY_SPARQL = "https://vocab.getty.edu/sparql"

# Known Getty Vocabularies IDs (common art movements and artists) - fallback
KNOWN_AAT = {
    "Impressionism": "300011147",
    "Post-Impressionism": "300021504",
    "Renaissance": "300020868",
    "Baroque": "300020449",
    "Rococo": "300020833",
    "Neoclassicism": "300021147",
    "Romanticism": "300021585",
    "Realism": "300021511",
    "Symbolism": "300021560",
    "Art Nouveau": "300021381",
    "Modernism": "300021474",
    "Expressionism": "300021540",
    "Cubism": "300021505",
    "Futurism": "300021558",
    "Constructivism": "300021617",
    "Dadaism": "300021567",
    "Surrealism": "300021524",
    "Abstract Expressionism": "300022676",
    "Pop Art": "300021801",
    "Minimalism": "300022976",
    "Contemporary art": "300015426",
    "Modern art": "300022994",
    "Painting": "300011008",
    "Sculpture": "300011994",
    "Drawing": "300011010",
    "Mannerism": "300021523",
    "Dutch and Flemish Renaissance painting": "300020868",
    "Northern Renaissance": "300020868",
    "High Renaissance": "300021172",
    "Dutch Golden Age painting": "300020868",
    "Baroque painting": "300020449",
    "Pre-Raphaelite Brotherhood": "300021811",
    "Neoclassicism": "300021147",
    "Aestheticism": "300021876",
    "Etruscan school": "300020868",
    "Classicism": "300021147",
    "Feminism": "300417961",
}

KNOWN_ULAN = {
    "Grigorescu, Nicolae": "500115369",
    "Van Gogh, Vincent": "500009943",
    "Tonitza, Nicolae": "500115399",
    "Picasso, Pablo": "500023818",
    "Matisse, Henri": "500018027",
    "Monet, Claude": "500018760",
    "Renoir, Pierre-Auguste": "500007575",
    "Caravaggio": "500018669",
    "Parmigianino": "500018730",
    "Angelica Kauffmann": "500115487",
    "Francisco Goya": "500013284",
    "Claude Monet": "500018760",
    "Vincent van Gogh": "500009943",
    "Frederic Leighton": "500018046",
    "Jacques-Louis David": "500012245",
    "Jan van Eyck": "500041392",
}

# Caching to avoid duplicate lookups
_getty_cache = {}

def search_aat_sparql(term):
    """
    Search AAT with SPARQL - dynamic lookup
    Returns: {'aat_id': str, 'aat_term': str, 'aat_url': str} or None
    """
    if not term or not isinstance(term, str):
        return None
    
    term = term.strip()
    
    # Try known terms first (faster)
    if term in KNOWN_AAT:
        return {
            "aat_id": KNOWN_AAT[term],
            "aat_term": term,
            "aat_url": f"http://vocab.getty.edu/page/aat/{KNOWN_AAT[term]}"
        }
    
    # Try SPARQL with retry logic
    for attempt in range(3):
        try:
            sparql = SPARQLWrapper(GETTY_SPARQL)
            sparql.setTimeout(30)  # 30 second timeout
            sparql.setReturnFormat(JSON)
            
            # Query for term (exact or partial match)
            query = f"""
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX luc: <http://www.ontotext.com/connectors/lucene#>
                PREFIX inst: <http://www.ontotext.com/owlim/inst#>
                SELECT ?id ?term WHERE {{
                    ?id a skos:Concept ;
                        luc:textIndex "{term}" ;
                        skos:inScheme <http://vocab.getty.edu/aat/> ;
                        skos:prefLabel ?term .
                    FILTER (lang(?term) = "en")
                }}
                LIMIT 1
            """
            
            sparql.setQuery(query)
            results = sparql.query().convert()
            
            if results.get("results", {}).get("bindings"):
                binding = results["results"]["bindings"][0]
                aat_id = binding["id"]["value"].split("/")[-1]
                aat_term = binding["term"]["value"]
                return {
                    "aat_id": aat_id,
                    "aat_term": aat_term,
                    "aat_url": f"http://vocab.getty.edu/page/aat/{aat_id}"
                }
            
            return None
            
        except Exception as e:
            if attempt < 2:
                wait_time = 2 * (attempt + 1)
                print(f"[GETTY AAT] Retry {attempt+1}/3 for '{term}' - waiting {wait_time}s: {str(e)[:50]}")
                time.sleep(wait_time)
            else:
                print(f"[GETTY AAT] Failed to lookup '{term}': {str(e)[:100]}")
                return None


def search_ulan_sparql(artist_name):
    """
    Search ULAN with SPARQL - dynamic lookup for artists
    Returns: {'ulan_id': str, 'ulan_name': str, 'ulan_url': str} or None
    """
    if not artist_name or not isinstance(artist_name, str):
        return None
    
    artist_name = artist_name.strip()
    
    # Try known artists first (faster)
    if artist_name in KNOWN_ULAN:
        return {
            "ulan_id": KNOWN_ULAN[artist_name],
            "ulan_name": artist_name,
            "ulan_url": f"http://vocab.getty.edu/page/ulan/{KNOWN_ULAN[artist_name]}"
        }
    
    # Try SPARQL with retry logic
    for attempt in range(3):
        try:
            sparql = SPARQLWrapper(GETTY_SPARQL)
            sparql.setTimeout(30)  # 30 second timeout
            sparql.setReturnFormat(JSON)
            
            # Query for artist (exact or partial match)
            query = f"""
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX luc: <http://www.ontotext.com/connectors/lucene#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?id ?name WHERE {{
                    ?id a skos:Concept ;
                        luc:textIndex "{artist_name}" ;
                        skos:inScheme <http://vocab.getty.edu/ulan/> ;
                        skos:prefLabel ?name .
                    FILTER (lang(?name) = "en")
                }}
                LIMIT 1
            """
            
            sparql.setQuery(query)
            results = sparql.query().convert()
            
            if results.get("results", {}).get("bindings"):
                binding = results["results"]["bindings"][0]
                ulan_id = binding["id"]["value"].split("/")[-1]
                ulan_name = binding["name"]["value"]
                return {
                    "ulan_id": ulan_id,
                    "ulan_name": ulan_name,
                    "ulan_url": f"http://vocab.getty.edu/page/ulan/{ulan_id}"
                }
            
            return None
            
        except Exception as e:
            if attempt < 2:
                wait_time = 2 * (attempt + 1)
                print(f"[GETTY ULAN] Retry {attempt+1}/3 for '{artist_name}' - waiting {wait_time}s: {str(e)[:50]}")
                time.sleep(wait_time)
            else:
                print(f"[GETTY ULAN] Failed to lookup '{artist_name}': {str(e)[:100]}")
                return None


def search_tgn_sparql(place_name):
    """
    Search TGN with SPARQL - dynamic lookup for places
    Returns: {'tgn_id': str, 'tgn_name': str, 'tgn_url': str} or None
    """
    if not place_name or not isinstance(place_name, str):
        return None
    
    place_name = place_name.strip()
    
    # Try SPARQL with retry logic
    for attempt in range(3):
        try:
            sparql = SPARQLWrapper(GETTY_SPARQL)
            sparql.setTimeout(30)
            sparql.setReturnFormat(JSON)
            
            # Simplified query without Lucene (more reliable)
            query = f"""
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX gvp: <http://vocab.getty.edu/ontology#>
                SELECT DISTINCT ?id ?name WHERE {{
                    ?id skos:inScheme <http://vocab.getty.edu/tgn/> ;
                        skos:prefLabel ?name .
                    FILTER (REGEX(STR(?name), "{place_name}", "i"))
                    FILTER (lang(?name) = "en")
                }}
                LIMIT 1
            """
            
            sparql.setQuery(query)
            results = sparql.query().convert()
            
            if results.get("results", {}).get("bindings"):
                binding = results["results"]["bindings"][0]
                tgn_id = binding["id"]["value"].split("/")[-1]
                tgn_name = binding["name"]["value"]
                print(f"[GETTY TGN] ✅ Found '{tgn_name}' -> {tgn_id}")
                return {
                    "tgn_id": tgn_id,
                    "tgn_name": tgn_name,
                    "tgn_url": f"http://vocab.getty.edu/page/tgn/{tgn_id}"
                }
            
            return None
            
        except Exception as e:
            if attempt < 2:
                wait_time = 2 * (attempt + 1)
                print(f"[GETTY TGN] Retry {attempt+1}/3 for '{place_name}' - waiting {wait_time}s: {str(e)[:50]}")
                time.sleep(wait_time)
            else:
                print(f"[GETTY TGN] Failed to lookup '{place_name}': {str(e)[:100]}")
                return None


def get_getty_enrichment(term, getty_type="aat"):
    """
    Cached Getty vocabulary lookup (AAT, ULAN, or TGN)
    Returns enrichment data or None
    
    Args:
        term: The term to lookup
        getty_type: "aat" (movements), "ulan" (artists), or "tgn" (places)
    """
    if not term:
        return None
    
    cache_key = f"{getty_type}:{term}"
    
    if cache_key in _getty_cache:
        return _getty_cache[cache_key]
    
    result = None
    if getty_type.lower() == "aat":
        result = search_aat_sparql(term)
    elif getty_type.lower() == "ulan":
        result = search_ulan_sparql(term)
    elif getty_type.lower() == "tgn":
        result = search_tgn_sparql(term)
    
    _getty_cache[cache_key] = result
    return result




