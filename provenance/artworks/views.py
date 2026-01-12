from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from .models import Artwork
from .dbpedia import get_author_details
from SPARQLWrapper import SPARQLWrapper, JSON
import json


def artworks_page(request):
    return render(request, "artworks_list.html")

def artworks_api(request):
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    offset = (page - 1) * per_page
    
    # Citim din Fuseki, nu din Wikidata
    sparql = SPARQLWrapper(settings.FUSEKI_ENDPOINT)
    
    # First, get total count
    sparql.setQuery("""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ex: <http://example.org/ontology/>
        SELECT (COUNT(?art) as ?count) WHERE {
            ?art rdf:type ex:Artwork .
        }
    """)
    sparql.setReturnFormat(JSON)
    count_results = sparql.query().convert()
    total = int(count_results["results"]["bindings"][0].get("count", {}).get("value", 0))
    
    # Then fetch ALL data (not paginated) to deduplicate
    sparql.setQuery(f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ex: <http://example.org/ontology/>
        SELECT ?title ?creatorFinal ?date ?museum ?movement ?birthDate ?birthPlace ?nationality ?creatorMovement WHERE {{
            ?art rdf:type ex:Artwork .
            OPTIONAL {{ ?art ex:title ?title }}
            OPTIONAL {{ ?art ex:creator ?creator }}
            OPTIONAL {{ ?art ex:createdBy ?artist . ?artist ex:name ?creatorName }}
            OPTIONAL {{ ?artist ex:birthDate ?birthDate }}
            OPTIONAL {{ ?artist ex:birthPlace ?birthPlace }}
            OPTIONAL {{ ?artist ex:nationality ?nationality }}
            OPTIONAL {{ ?artist ex:movement ?creatorMovement }}
            OPTIONAL {{ ?art ex:date ?date }}
            OPTIONAL {{ ?art ex:movement ?movement }}
            OPTIONAL {{ ?art ex:museum ?museum }}
            BIND(COALESCE(?creator, ?creatorName, "Necunoscut") AS ?creatorFinal)
        }}
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # Deduplicate by (title, date) - merge multi-valued properties
    deduped_dict = {}
    for r in results["results"]["bindings"]:
        title = r.get("title", {}).get("value") or "N/A"
        creator = r.get("creatorFinal", {}).get("value") or "Necunoscut"
        date = r.get("date", {}).get("value")
        museum = r.get("museum", {}).get("value")
        movement = r.get("movement", {}).get("value")
        creator_movement = r.get("creatorMovement", {}).get("value")
        birthDate = r.get("birthDate", {}).get("value")
        birthPlace = r.get("birthPlace", {}).get("value")
        nationality = r.get("nationality", {}).get("value")
        
        key = (title, date)
        
        if key not in deduped_dict:
            deduped_dict[key] = {
                "title": title,
                "creators": {creator} if creator and creator != "Necunoscut" else set(),
                "date": date,
                "museums": {museum} if museum else set(),
                "movements": {movement} if movement else set(),
                "creator_movements": {creator_movement} if creator_movement else set(),
                "birth_dates": {birthDate} if birthDate else set(),
                "birth_places": {birthPlace} if birthPlace else set(),
                "nationalities": {nationality} if nationality else set(),
            }
        else:
            # Merge multi-valued fields
            item = deduped_dict[key]
            if creator and creator != "Necunoscut":
                item["creators"].add(creator)
            if museum:
                item["museums"].add(museum)
            if movement:
                item["movements"].add(movement)
            if creator_movement:
                item["creator_movements"].add(creator_movement)
            if birthDate:
                item["birth_dates"].add(birthDate)
            if birthPlace:
                item["birth_places"].add(birthPlace)
            if nationality:
                item["nationalities"].add(nationality)
    
    # Apply pagination on deduplicated data
    deduped_list = list(deduped_dict.values())
    total = len(deduped_list)
    paginated_data = deduped_list[offset:offset + per_page]
    
    # Convert sets to sorted lists for JSON serialization
    data = []
    for item in paginated_data:
        creators_list = sorted([c for c in item["creators"] if c])
        processed_item = {
            "title": item["title"],
            "creators": creators_list,
            "creator": creators_list[0] if creators_list else "Necunoscut",
            "date": item["date"],
            "museums": sorted([m for m in item["museums"] if m]),
            "movements": sorted([m for m in item["movements"] if m]),
            "creator_movements": sorted([m for m in item["creator_movements"] if m]),
            "birth_dates": sorted([bd for bd in item["birth_dates"] if bd]),
            "birth_places": sorted([bp for bp in item["birth_places"] if bp]),
            "nationalities": sorted([n for n in item["nationalities"] if n]),
        }
        
        # Build backward-compatible structure
        processed_item["museum"] = processed_item["museums"][0] if processed_item["museums"] else None
        processed_item["movement"] = processed_item["movements"][0] if processed_item["movements"] else None
        
        if any([processed_item["birth_dates"], processed_item["birth_places"], processed_item["nationalities"], processed_item["creator_movements"]]):
            processed_item["dbpedia"] = {
                "birthDate": processed_item["birth_dates"][0] if processed_item["birth_dates"] else None,
                "birthPlace": processed_item["birth_places"][0] if processed_item["birth_places"] else None,
                "nationality": processed_item["nationalities"][0] if processed_item["nationalities"] else None,
                "movement": processed_item["creator_movements"][0] if processed_item["creator_movements"] else None,
            }
        
        data.append(processed_item)

    return JsonResponse({
        "items": data,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    })


def sparql_endpoint(request):
    """Public SPARQL endpoint - accepts GET/POST with 'query' parameter"""
    if request.method == 'GET':
        query = request.GET.get('query', '')
    elif request.method == 'POST':
        query = request.POST.get('query', '')
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    if not query:
        # Return HTML form if no query provided
        return render(request, "sparql_endpoint.html")
    
    try:
        sparql = SPARQLWrapper(settings.FUSEKI_ENDPOINT)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return JsonResponse(results, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def statistics_page(request):
    """Statistics page with visualizations"""
    return render(request, "statistics.html")


def statistics_api(request):
    """Pre-computed statistics about artworks"""
    try:
        sparql = SPARQLWrapper(settings.FUSEKI_ENDPOINT)
        
        stats = {}
        
        # 1. Total artworks
        sparql.setQuery("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ex: <http://example.org/ontology/>
            SELECT (COUNT(DISTINCT ?art) as ?total) WHERE {
                ?art rdf:type ex:Artwork .
            }
        """)
        sparql.setReturnFormat(JSON)
        result = sparql.query().convert()
        stats["total_artworks"] = int(result["results"]["bindings"][0]["total"]["value"])
        
        # 2. Top 10 creators
        sparql.setQuery("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ex: <http://example.org/ontology/>
            SELECT ?creator (COUNT(?art) as ?count) WHERE {
                ?art rdf:type ex:Artwork ;
                     ex:creator ?creator .
            }
            GROUP BY ?creator
            ORDER BY DESC(?count)
            LIMIT 10
        """)
        result = sparql.query().convert()
        stats["top_creators"] = [
            {"creator": b["creator"]["value"], "count": int(b["count"]["value"])}
            for b in result["results"]["bindings"]
        ]
        
        # 3. Top 10 museums (excluding None/null values)
        sparql.setQuery("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ex: <http://example.org/ontology/>
            SELECT ?museum (COUNT(?art) as ?count) WHERE {
                ?art rdf:type ex:Artwork ;
                     ex:museum ?museum .
                FILTER(?museum != "" && ?museum != "None")
            }
            GROUP BY ?museum
            ORDER BY DESC(?count)
            LIMIT 10
        """)
        result = sparql.query().convert()
        stats["top_museums"] = [
            {"museum": b["museum"]["value"], "count": int(b["count"]["value"])}
            for b in result["results"]["bindings"]
        ]
        
        # 4. Top movements (excluding None/null values)
        sparql.setQuery("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ex: <http://example.org/ontology/>
            SELECT ?movement (COUNT(?art) as ?count) WHERE {
                ?art rdf:type ex:Artwork ;
                     ex:movement ?movement .
                FILTER(?movement != "" && ?movement != "None")
            }
            GROUP BY ?movement
            ORDER BY DESC(?count)
            LIMIT 10
        """)
        result = sparql.query().convert()
        stats["top_movements"] = [
            {"movement": b["movement"]["value"], "count": int(b["count"]["value"])}
            for b in result["results"]["bindings"]
        ]
        
        # 5. Artworks by century
        sparql.setQuery("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ex: <http://example.org/ontology/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT ?century (COUNT(?art) as ?count) WHERE {
                ?art rdf:type ex:Artwork ;
                     ex:date ?date .
                FILTER(STRLEN(STR(?date)) >= 4)
                FILTER(REGEX(STR(?date), "^[0-9]{4}"))
                BIND(FLOOR(xsd:integer(SUBSTR(STR(?date), 1, 4)) / 100) * 100 as ?century)
            }
            GROUP BY ?century
            ORDER BY ?century
        """)
        result = sparql.query().convert()
        stats["by_century"] = [
            {"century": f"{b['century']['value']}s", "count": int(b["count"]["value"])}
            for b in result["results"]["bindings"]
        ]
        
        # 6. Museum breakdown - for each museum, count artworks and list top movements
        sparql.setQuery("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ex: <http://example.org/ontology/>
            SELECT ?museum (COUNT(?art) as ?count) WHERE {
                ?art rdf:type ex:Artwork ;
                     ex:museum ?museum .
                FILTER(?museum != "" && ?museum != "None")
            }
            GROUP BY ?museum
            ORDER BY DESC(?count)
        """)
        result = sparql.query().convert()
        museums = [
            {"museum": b["museum"]["value"], "count": int(b["count"]["value"])}
            for b in result["results"]["bindings"]
        ]
        
        # For each museum, get top movements
        museum_breakdown = []
        for museum_data in museums:
            museum_name = museum_data["museum"]
            museum_total = museum_data["count"]
            
            # Query movements for this museum (excluding empty movements and "None")
            sparql.setQuery(f"""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX ex: <http://example.org/ontology/>
                SELECT ?movement (COUNT(?art) as ?movement_count) WHERE {{
                    ?art rdf:type ex:Artwork ;
                         ex:museum "{museum_name}" ;
                         ex:movement ?movement .
                    FILTER(?movement != "" && ?movement != "None")
                }}
                GROUP BY ?movement
                ORDER BY DESC(?movement_count)
                LIMIT 5
            """)
            result = sparql.query().convert()
            movements = [
                {"movement": b["movement"]["value"], "movement_count": int(b["movement_count"]["value"])}
                for b in result["results"]["bindings"]
            ]
            
            museum_breakdown.append({
                "museum": museum_name,
                "total_artworks": museum_total,
                "top_movements": movements
            })
        
        stats["museum_breakdown"] = museum_breakdown
        
        return JsonResponse(stats, safe=False)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[STATISTICS ERROR] {error_details}")
        return JsonResponse({
            "error": str(e), 
            "message": f"Error: {str(e)[:200]}. Check Django console for full details.",
            "endpoint": settings.FUSEKI_ENDPOINT
        }, status=500)

def romanian_heritage_page(request):
    """Romanian heritage artworks page"""
    return render(request, "romanian_heritage.html")


def romanian_heritage_api(request):
    """Romanian heritage artworks API"""
    # Query Fuseki for Romanian artworks (marked with heritage=true and source=data.gov.ro)
    sparql = SPARQLWrapper(settings.FUSEKI_ENDPOINT)
    sparql.setQuery("""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ex: <http://example.org/ontology/>
        SELECT ?title ?creator ?date ?museum ?movement ?birthDate ?birthPlace ?nationality ?creatorMovement WHERE {
            ?art rdf:type ex:Artwork .
            ?art ex:creator ?creator .
            ?art ex:heritage "true" .
            ?art ex:source "data.gov.ro" .
            OPTIONAL { ?art ex:title ?title }
            OPTIONAL { ?art ex:date ?date }
            OPTIONAL { ?art ex:museum ?museum }
            OPTIONAL { ?art ex:movement ?movement }
            OPTIONAL { ?art ex:createdBy ?artist . ?artist ex:birthDate ?birthDate }
            OPTIONAL { ?art ex:createdBy ?artist . ?artist ex:birthPlace ?birthPlace }
            OPTIONAL { ?art ex:createdBy ?artist . ?artist ex:nationality ?nationality }
            OPTIONAL { ?art ex:createdBy ?artist . ?artist ex:movement ?creatorMovement }
        }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # Deduplicate by (title, date) - same artwork regardless of creator
    # Merge ALL multi-valued properties on same artwork
    deduped_dict = {}
    for r in results["results"]["bindings"]:
        title = r.get("title", {}).get("value") or "N/A"
        creator = r.get("creator", {}).get("value") or "Necunoscut"
        date = r.get("date", {}).get("value")
        museum = r.get("museum", {}).get("value")
        movement = r.get("movement", {}).get("value")
        creator_movement = r.get("creatorMovement", {}).get("value")
        birthDate = r.get("birthDate", {}).get("value")
        birthPlace = r.get("birthPlace", {}).get("value")
        nationality = r.get("nationality", {}).get("value")
        
        key = (title, date)
        
        if key not in deduped_dict:
            deduped_dict[key] = {
                "title": title,
                "creators": {creator} if creator and creator != "Necunoscut" else set(),
                "date": date,
                "museums": {museum} if museum else set(),
                "movements": {movement} if movement else set(),
                "creator_movements": {creator_movement} if creator_movement else set(),
                "birth_dates": {birthDate} if birthDate else set(),
                "birth_places": {birthPlace} if birthPlace else set(),
                "nationalities": {nationality} if nationality else set(),
            }
        else:
            # Merge multi-valued fields
            item = deduped_dict[key]
            if creator and creator != "Necunoscut":
                item["creators"].add(creator)
            if museum:
                item["museums"].add(museum)
            if movement:
                item["movements"].add(movement)
            if creator_movement:
                item["creator_movements"].add(creator_movement)
            if birthDate:
                item["birth_dates"].add(birthDate)
            if birthPlace:
                item["birth_places"].add(birthPlace)
            if nationality:
                item["nationalities"].add(nationality)
    
    # Convert sets to sorted lists and build response
    data = []
    for item in deduped_dict.values():
        creators_list = sorted([c for c in item["creators"] if c])
        processed_item = {
            "title": item["title"],
            "creators": creators_list,
            "creator": creators_list[0] if creators_list else "Necunoscut",
            "date": item["date"],
            "museums": sorted([m for m in item["museums"] if m]),
            "movements": sorted([m for m in item["movements"] if m]),
            "creator_movements": sorted([m for m in item["creator_movements"] if m]),
            "birth_dates": sorted([bd for bd in item["birth_dates"] if bd]),
            "birth_places": sorted([bp for bp in item["birth_places"] if bp]),
            "nationalities": sorted([n for n in item["nationalities"] if n]),
        }
        
        # Build backward-compatible structure
        processed_item["museum"] = processed_item["museums"][0] if processed_item["museums"] else None
        processed_item["movement"] = processed_item["movements"][0] if processed_item["movements"] else None
        
        if any([processed_item["birth_dates"], processed_item["birth_places"], processed_item["nationalities"], processed_item["creator_movements"]]):
            processed_item["dbpedia"] = {
                "birthDate": processed_item["birth_dates"][0] if processed_item["birth_dates"] else None,
                "birthPlace": processed_item["birth_places"][0] if processed_item["birth_places"] else None,
                "nationality": processed_item["nationalities"][0] if processed_item["nationalities"] else None,
                "movement": processed_item["creator_movements"][0] if processed_item["creator_movements"] else None,
            }
        
        data.append(processed_item)

    return JsonResponse(data, safe=False)