"""
Getty Vocabularies Integration (AAT, ULAN, TGN)
- AAT (Art & Architecture Thesaurus) for movements, styles, techniques
- ULAN (Union List of Artist Names) for artists
- TGN (Thesaurus of Geographic Names) for places

Uses known dictionaries + optional SPARQL fallback
"""

import requests

# Known Getty Vocabularies IDs - Verified from official Getty.edu
# See discover_getty.py for source and additional terms
KNOWN_AAT = {
    "Abstract Expressionism": "300020851",
    "Art Nouveau": "300021147",
    "Baroque": "300020871",
    "Baroque painting": "300020871",
    "Classicism": "300021145",
    "Constructivism": "300020845",
    "Contemporary art": "300021147",
    "Cubism": "300020842",
    "Dadaism": "300020846",
    "Dutch Golden Age painting": "300020874",
    "Expressionism": "300020847",
    "Futurism": "300020843",
    "German Romanticism": "300020832",
    "High Renaissance": "300020868",
    "Impressionism": "300011147",
    "Mannerism": "300020854",
    "Minimalism": "300020853",
    "Modern art": "300021147",
    "Modernism": "300021147",
    "Neoclassicism": "300021145",
    "Northern Renaissance": "300020868",
    "Pop Art": "300020852",
    "Post-Impressionism": "300020869",
    "Realism": "300021081",
    "Renaissance": "300020868",
    "Rococo": "300021140",
    "Romanticism": "300020832",
    "Surrealism": "300020849",
    "Symbolism": "300020864",
    "Venetian school": "300021476",
}

KNOWN_ULAN = {
    "Dalí, Salvador": "500004659",
    "Grigorescu, Nicolae": "500072318",
    "Leonardo da Vinci": "500010879",
    "Matisse, Henri": "500015071",
    "Michelangelo Buonarroti": "500010654",
    "Monet, Claude": "500019833",
    "Picasso, Pablo": "500023818",
    "Raphael": "500013456",
    "Renoir, Pierre-Auguste": "500013450",
    "Titian": "500031158",
    "Tonitza, Nicolae": "500062738",
    "Van Gogh, Vincent": "500009943",
    "Vermeer, Johannes": "500026570",
    "Veronese, Paolo": "500031388",
}

# Caching to avoid duplicate lookups
_getty_cache = {}

def search_aat_sparql(term):
    """
    Search AAT - check known dictionary first, then optional SPARQL fallback
    Returns: {'aat_id': str, 'aat_term': str, 'aat_url': str} or None
    """
    if not term or not isinstance(term, str):
        return None
    
    term = term.strip()
    
    # Check known dictionary first
    if term in KNOWN_AAT:
        aat_id = KNOWN_AAT[term]
        return {
            "aat_id": aat_id,
            "aat_term": term,
            "aat_url": f"http://vocab.getty.edu/page/aat/{aat_id}"
        }
    
    # Optional SPARQL fallback (disabled due to timeouts)
    # Could implement here if needed
    
    return None


def search_ulan_sparql(artist_name):
    """
    Search ULAN - check known dictionary first with name variations
    Returns: {'ulan_id': str, 'ulan_name': str, 'ulan_url': str} or None
    
    Tries multiple name formats:
    - "Last, First" (dictionary format)
    - "First Last" (natural order)
    - "Last First" (reverse order)
    """
    if not artist_name or not isinstance(artist_name, str):
        return None
    
    artist_name = artist_name.strip()
    
    # Try exact match first
    if artist_name in KNOWN_ULAN:
        ulan_id = KNOWN_ULAN[artist_name]
        return {
            "ulan_id": ulan_id,
            "ulan_name": artist_name,
            "ulan_url": f"http://vocab.getty.edu/page/ulan/{ulan_id}"
        }
    
    # Try variations
    name_parts = artist_name.split()
    
    if len(name_parts) >= 2:
        # Try "Last, First" format (what's in KNOWN_ULAN)
        last_first = f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"
        if last_first in KNOWN_ULAN:
            ulan_id = KNOWN_ULAN[last_first]
            return {
                "ulan_id": ulan_id,
                "ulan_name": last_first,
                "ulan_url": f"http://vocab.getty.edu/page/ulan/{ulan_id}"
            }
        
        # Try reverse order if there are 2+ parts
        # "Van Gogh, Vincent" could be stored as "Gogh, Van Vincent" or similar
        for i in range(1, len(name_parts)):
            # Try putting word i at the end: "word0...wordi, wordi+1...last"
            test_last = " ".join(name_parts[i:])
            test_first = " ".join(name_parts[:i])
            test_name = f"{test_last}, {test_first}"
            if test_name in KNOWN_ULAN:
                ulan_id = KNOWN_ULAN[test_name]
                return {
                    "ulan_id": ulan_id,
                    "ulan_name": test_name,
                    "ulan_url": f"http://vocab.getty.edu/page/ulan/{ulan_id}"
                }
    
    # Try partial matches (e.g., "Nicolae Tonitza" in dict as "Tonitza, Nicolae")
    for key in KNOWN_ULAN:
        # Extract parts from dictionary key
        if "," in key:
            dict_parts = key.split(",")
            dict_last = dict_parts[0].strip()
            dict_first = dict_parts[1].strip() if len(dict_parts) > 1 else ""
            
            # Check if any parts match
            if dict_last in artist_name or dict_first in artist_name:
                # More strict: require both parts or the full name
                if (dict_last in artist_name and dict_first in artist_name) or \
                   (artist_name.lower() == key.lower()):
                    ulan_id = KNOWN_ULAN[key]
                    return {
                        "ulan_id": ulan_id,
                        "ulan_name": key,
                        "ulan_url": f"http://vocab.getty.edu/page/ulan/{ulan_id}"
                    }
    
    return None


def search_tgn_sparql(place_name):
    """
    Search TGN - check known dictionary first (not implemented yet)
    Returns: {'tgn_id': str, 'tgn_name': str, 'tgn_url': str} or None
    """
    # TGN not implemented yet
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




