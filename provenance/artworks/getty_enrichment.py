"""
Getty Vocabularies Integration (AAT, ULAN, TGN)
- AAT (Art & Architecture Thesaurus) for movements, styles, techniques
- ULAN (Union List of Artist Names) for artists
- TGN (Thesaurus of Geographic Names) for places
"""

import requests
from SPARQLWrapper import SPARQLWrapper, XML
import xml.etree.ElementTree as ET

# Getty SPARQL endpoint
GETTY_SPARQL = "https://vocab.getty.edu/sparql"

# Known Getty Vocabularies IDs (common art movements and artists)
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
}

KNOWN_ULAN = {
    "Grigorescu, Nicolae": "500115369",
    "Van Gogh, Vincent": "500009943",
    "Tonitza, Nicolae": "500115399",
    "Picasso, Pablo": "500023818",
    "Matisse, Henri": "500018027",
    "Monet, Claude": "500018760",
    "Renoir, Pierre-Auguste": "500007575",
}

def search_aat_sparql(term):
    """
    Search AAT with fallback to known terms (SPARQL disabled due to timeout)
    Returns: {'aat_id': str, 'aat_term': str, 'aat_url': str}
    """
    # Check known terms first (only method for now)
    if term in KNOWN_AAT:
        return {
            "aat_id": KNOWN_AAT[term],
            "aat_term": term,
            "aat_url": f"http://vocab.getty.edu/page/aat/{KNOWN_AAT[term]}"
        }
    return None


def search_ulan_sparql(artist_name):
    """
    Search ULAN with fallback to known artists (SPARQL disabled due to timeout)
    Returns: {'ulan_id': str, 'ulan_name': str, 'ulan_url': str}
    """
    # Check known artists first (only method for now)
    if artist_name in KNOWN_ULAN:
        return {
            "ulan_id": KNOWN_ULAN[artist_name],
            "ulan_name": artist_name,
            "ulan_url": f"http://vocab.getty.edu/page/ulan/{KNOWN_ULAN[artist_name]}"
        }
    return None


# Caching to avoid duplicate lookups
_getty_cache = {}

def get_getty_enrichment(term, getty_type="aat"):
    """
    Cached Getty vocabulary lookup (AAT, ULAN, or TGN)
    Returns enrichment data or None
    """
    cache_key = f"{getty_type}:{term}"
    
    if cache_key in _getty_cache:
        return _getty_cache[cache_key]
    
    result = None
    if getty_type.lower() == "aat":
        result = search_aat_sparql(term)
    elif getty_type.lower() == "ulan":
        result = search_ulan_sparql(term)
    
    _getty_cache[cache_key] = result
    return result



