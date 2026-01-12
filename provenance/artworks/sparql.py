from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from django.conf import settings
import socket
import urllib.error as urlerror

EX = Namespace("http://example.org/ontology/")

WD_TIMEOUT = 60
WD_RETRY = 5
WD_USER_AGENT = "provenance-app/1.0 (contact: example@example.com)"

def _make_wikidata_client():
    client = SPARQLWrapper("https://query.wikidata.org/sparql")
    client.setReturnFormat(JSON)
    client.setTimeout(WD_TIMEOUT)
    client.addCustomHttpHeader("User-Agent", WD_USER_AGENT)
    client.setMethod(POST)
    return client

def get_paintings(limit: int = 10, total: int = 100):
    sparql = _make_wikidata_client()
    all_bindings = []

    for offset in range(0, total, limit):
        sparql.setQuery(f"""
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?item ?creator ?inception ?birthDate ?birthPlace ?collection ?location ?movement ?nationality ?creatorMovement WHERE {{
                ?item wdt:P31 wd:Q3305213.
                OPTIONAL {{ ?item wdt:P170 ?creator. }}
                OPTIONAL {{ ?item wdt:P571 ?inception }}
                OPTIONAL {{ ?item wdt:P195 ?collection }}
                OPTIONAL {{ ?item wdt:P276 ?location }}
                OPTIONAL {{ ?item wdt:P135 ?movement }}
                OPTIONAL {{ ?creator wdt:P569 ?birthDate }}
                OPTIONAL {{ ?creator wdt:P19 ?birthPlace }}
                OPTIONAL {{ ?creator wdt:P27 ?nationality }}
                OPTIONAL {{ ?creator wdt:P135 ?creatorMovement }}
            }}
            LIMIT {limit} OFFSET {offset}
            """)

        results = None
        for attempt in range(WD_RETRY):
            try:
                results = sparql.query().convert()
                print(f"[WIKIDATA SUCCESS] batch offset {offset} on attempt {attempt+1}")
                break
            except (socket.timeout, urlerror.HTTPError, urlerror.URLError) as e:
                wait_time = 1 * (attempt + 1)  # 1s, 2s, 3s, 4s, 5s
                print(f"[WIKIDATA RETRY {attempt+1}] {e} - waiting {wait_time}s")
                import time
                time.sleep(wait_time)
            except Exception as e:
                print(f"[WIKIDATA ERROR] {e}")
                break
        if results is None:
            print(f"[WIKIDATA FAIL] skipping batch offset {offset}")
            continue

        batch = results.get("results", {}).get("bindings", [])
        if not batch:
            break  # no more data
        all_bindings.extend(batch)

    if not all_bindings:
        print("[WIKIDATA FAIL] No results; returning empty list")
        return []

    item_uris = set()
    creator_uris = set()
    place_uris = set()
    movement_uris = set()
    creator_movement_uris = set()
    nationality_uris = set()
    for item in all_bindings:
        item_uri = item.get("item", {}).get("value")
        creator_uri = item.get("creator", {}).get("value")
        birth_place_uri = item.get("birthPlace", {}).get("value")
        collection_uri = item.get("collection", {}).get("value")
        location_uri = item.get("location", {}).get("value")
        movement_uri = item.get("movement", {}).get("value")
        creator_movement_uri = item.get("creatorMovement", {}).get("value")
        nationality_uri = item.get("nationality", {}).get("value")
        if item_uri:
            item_uris.add(item_uri)
        if creator_uri:
            creator_uris.add(creator_uri)
        if birth_place_uri:
            place_uris.add(birth_place_uri)
        if collection_uri:
            place_uris.add(collection_uri)
        if location_uri:
            place_uris.add(location_uri)
        if movement_uri:
            movement_uris.add(movement_uri)
        if creator_movement_uri:
            creator_movement_uris.add(creator_movement_uri)
        if nationality_uri:
            nationality_uris.add(nationality_uri)

    print(f"[WIKIDATA] fetched {len(item_uris)} items, {len(creator_uris)} creators")
    
    # Fetch labels for all URIs
    labels = {}
    for uri in (item_uris | creator_uris | place_uris | movement_uris | creator_movement_uris | nationality_uris):
        try:
            label_client = _make_wikidata_client()
            label_client.setQuery(f"""
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?label WHERE {{
                    <{uri}> rdfs:label ?label.
                    FILTER(lang(?label) = "en")
                }} LIMIT 1
            """)
            label_result = label_client.query().convert()
            if label_result["results"]["bindings"]:
                label_val = label_result["results"]["bindings"][0]["label"]["value"]
                if len(label_val) < 50:
                    labels[uri] = label_val

        except Exception as e:
            print(f"[LABEL FETCH] failed for {uri}: {e}")
    
    g = Graph()
    g.bind("ex", EX)
    triple_count = 0
    batch_size = 50

    data = []
    for item in all_bindings:
        item_uri = item.get("item", {}).get("value")
        creator_uri = item.get("creator", {}).get("value")
        title = labels.get(item_uri, "Unknown")
        author = labels.get(creator_uri, "Necunoscut") if creator_uri else "Necunoscut"
        date_raw = item.get("inception", {}).get("value")
        birthDate_raw = item.get("birthDate", {}).get("value")
        birthPlace_uri = item.get("birthPlace", {}).get("value")
        collection_uri = item.get("collection", {}).get("value")
        location_uri = item.get("location", {}).get("value")
        movement_uri = item.get("movement", {}).get("value")
        creator_movement_uri = item.get("creatorMovement", {}).get("value")
        nationality_uri = item.get("nationality", {}).get("value")

        date = date_raw.split("T")[0] if date_raw else None
        birthDate = birthDate_raw.split("T")[0] if birthDate_raw else None
        birthPlace = labels.get(birthPlace_uri) if birthPlace_uri else None
        museum = labels.get(collection_uri) or labels.get(location_uri) if (collection_uri or location_uri) else None
        movement = labels.get(movement_uri) if movement_uri else None
        creator_movement = labels.get(creator_movement_uri) if creator_movement_uri else None
        nationality = labels.get(nationality_uri) if nationality_uri else None

        if title == "Unknown":
            if author and author != "Necunoscut":
                title = f"{author} artwork" if not date else f"{author} ({date})"
            else:
                title = item_uri.split("/")[-1] if item_uri else "Unknown_item"
                if title == "Unknown_item":
                    continue

        art_uri = URIRef(EX[title.replace(" ", "_")])
        artist_uri = URIRef(EX[author.replace(" ", "_")])

        # Triples
        g.add((art_uri, RDF.type, EX.Artwork))
        triple_count += 1
        if title:
            g.add((art_uri, EX.title, Literal(title, datatype=XSD.string)))
            triple_count += 1
        g.add((art_uri, EX.createdBy, artist_uri))
        triple_count += 1
        g.add((artist_uri, RDF.type, EX.Artist))
        triple_count += 1
        g.add((artist_uri, EX.name, Literal(author, datatype=XSD.string)))
        triple_count += 1
        if date:
            g.add((art_uri, EX.date, Literal(date, datatype=XSD.string)))
            triple_count += 1
        if museum:
            g.add((art_uri, EX.museum, Literal(museum, datatype=XSD.string)))
            triple_count += 1
        if movement:
            g.add((art_uri, EX.movement, Literal(movement, datatype=XSD.string)))
            triple_count += 1
        if birthDate:
            g.add((artist_uri, EX.birthDate, Literal(birthDate, datatype=XSD.string)))
            triple_count += 1
        if birthPlace:
            g.add((artist_uri, EX.birthPlace, Literal(birthPlace, datatype=XSD.string)))
            triple_count += 1
        if nationality:
            g.add((artist_uri, EX.nationality, Literal(nationality, datatype=XSD.string)))
            triple_count += 1
        if creator_movement:
            g.add((artist_uri, EX.movement, Literal(creator_movement, datatype=XSD.string)))
            triple_count += 1

        if triple_count >= batch_size:
            if len(g):
                push_graph_to_fuseki(g)
            g = Graph()
            g.bind("ex", EX)
            triple_count = 0

        birthDateVal = birthDate
        birthPlaceVal = birthPlace
        nationalityVal = nationality
        if not (birthDateVal or birthPlaceVal or nationalityVal):
            try:
                from .models import DBpediaArtist
                artist = DBpediaArtist.objects.get(name=author)
                birthDateVal = artist.birthDate or birthDateVal
                birthPlaceVal = artist.birthPlace or birthPlaceVal
                nationalityVal = artist.nationality or nationalityVal
            except (Exception):
                pass

        data.append({
            "title": title,
            "creator": author,
            "date": date,
            "museum": museum,
            "movement": movement,
            "dbpedia": {
                "birthDate": birthDateVal,
                "birthPlace": birthPlaceVal,
                "nationality": nationalityVal,
                "movement": creator_movement,
            }
        })

    if len(g):
        push_graph_to_fuseki(g)


    seen = {}
    for item in data:
        key = (item["title"], item["date"])
        if key not in seen:
            item["creators"] = {item["creator"]} if item["creator"] and item["creator"] != "Necunoscut" else set()
            item["movements"] = {item["movement"]} if item["movement"] else set()
            item["museums"] = {item["museum"]} if item["museum"] else set()
            item["creator_movements"] = {item["dbpedia"]["movement"]} if item["dbpedia"]["movement"] else set()
            item["nationalities"] = {item["dbpedia"]["nationality"]} if item["dbpedia"]["nationality"] else set()
            item["birth_dates"] = {item["dbpedia"]["birthDate"]} if item["dbpedia"]["birthDate"] else set()
            item["birth_places"] = {item["dbpedia"]["birthPlace"]} if item["dbpedia"]["birthPlace"] else set()
            seen[key] = item
        else:
            existing = seen[key]
            if item["creator"] and item["creator"] != "Necunoscut":
                existing["creators"].add(item["creator"])
            if item["movement"]:
                existing["movements"].add(item["movement"])
            if item["museum"]:
                existing["museums"].add(item["museum"])
            if item["dbpedia"]["movement"]:
                existing["creator_movements"].add(item["dbpedia"]["movement"])
            if item["dbpedia"]["nationality"]:
                existing["nationalities"].add(item["dbpedia"]["nationality"])
            if item["dbpedia"]["birthDate"]:
                existing["birth_dates"].add(item["dbpedia"]["birthDate"])
            if item["dbpedia"]["birthPlace"]:
                existing["birth_places"].add(item["dbpedia"]["birthPlace"])

    deduped_data = list(seen.values())
    print(f"[WIKIDATA] Deduplicated: {len(data)} raw results → {len(deduped_data)} unique artworks")
    return deduped_data


def push_graph_to_fuseki(graph: Graph):
    update_endpoint = settings.FUSEKI_UPDATE
    serialized = graph.serialize(format='nt')
    data = serialized.decode("utf-8") if isinstance(serialized, bytes) else str(serialized)

    for attempt in range(3):
        try:
            sparql = SPARQLWrapper(update_endpoint)
            sparql.setMethod(POST)
            sparql.setQuery("""
                INSERT DATA { %s }
            """ % data)
            sparql.query()
            print(f"[FUSEKI] pushed {len(graph)} triples")
            return
        except Exception as e:
            wait_time = 1 * (attempt + 1)
            print(f"[FUSEKI RETRY {attempt+1}] {e} - waiting {wait_time}s")
            import time
            time.sleep(wait_time)

def get_romanian_artworks(limit: int = 10, total: int = 100):
    sparql = _make_wikidata_client()
    all_bindings = []

    for offset in range(0, total, limit):
        sparql.setQuery(f"""
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?item ?creator ?inception ?birthDate ?birthPlace ?collection ?location ?movement ?nationality ?creatorMovement ?country WHERE {{
                ?item wdt:P31 wd:Q3305213.
                {{
                    ?item wdt:P17 wd:Q218.
                }} UNION {{
                    ?item wdt:P170 ?creator.
                    ?creator wdt:P27 wd:Q218.
                }}
                OPTIONAL {{ ?item wdt:P170 ?creator. }}
                OPTIONAL {{ ?item rdfs:label ?itemLabel. FILTER(lang(?itemLabel) = "en") }}
                OPTIONAL {{ ?item wdt:P571 ?inception }}
                OPTIONAL {{ ?item wdt:P195 ?collection }}
                OPTIONAL {{ ?item wdt:P276 ?location }}
                OPTIONAL {{ ?item wdt:P135 ?movement }}
                OPTIONAL {{ ?item wdt:P17 ?country }}
                OPTIONAL {{ ?creator wdt:P569 ?birthDate }}
                OPTIONAL {{ ?creator wdt:P19 ?birthPlace }}
                OPTIONAL {{ ?creator wdt:P27 ?nationality }}
                OPTIONAL {{ ?creator wdt:P135 ?creatorMovement }}
            }} LIMIT {limit} OFFSET {offset}
            """)

        results = None
        for attempt in range(WD_RETRY):
            try:
                results = sparql.query().convert()
                print(f"[WIKIDATA ROMANIAN] batch offset {offset} on attempt {attempt+1}")
                break
            except (socket.timeout, urlerror.HTTPError, urlerror.URLError) as e:
                wait_time = 1 * (attempt + 1)
                print(f"[WIKIDATA ROMANIAN RETRY {attempt+1}] {e} - waiting {wait_time}s")
                import time
                time.sleep(wait_time)
            except Exception as e:
                print(f"[WIKIDATA ROMANIAN ERROR] {e}")
                break

        if results:
            all_bindings.extend(results["results"]["bindings"])

    item_uris = set()
    creator_uris = set()
    place_uris = set()
    movement_uris = set()
    creator_movement_uris = set()
    nationality_uris = set()
    
    for item in all_bindings:
        item_uri = item.get("item", {}).get("value")
        creator_uri = item.get("creator", {}).get("value")
        birth_place_uri = item.get("birthPlace", {}).get("value")
        collection_uri = item.get("collection", {}).get("value")
        location_uri = item.get("location", {}).get("value")
        movement_uri = item.get("movement", {}).get("value")
        creator_movement_uri = item.get("creatorMovement", {}).get("value")
        nationality_uri = item.get("nationality", {}).get("value")
        if item_uri:
            item_uris.add(item_uri)
        if creator_uri:
            creator_uris.add(creator_uri)
        if birth_place_uri:
            place_uris.add(birth_place_uri)
        if collection_uri:
            place_uris.add(collection_uri)
        if location_uri:
            place_uris.add(location_uri)
        if movement_uri:
            movement_uris.add(movement_uri)
        if creator_movement_uri:
            creator_movement_uris.add(creator_movement_uri)
        if nationality_uri:
            nationality_uris.add(nationality_uri)

    print(f"[WIKIDATA ROMANIAN] fetched {len(item_uris)} items, {len(creator_uris)} creators")

    # Fetch labels
    labels = {}
    for uri in (item_uris | creator_uris | place_uris | movement_uris | creator_movement_uris | nationality_uris):
        try:
            label_client = _make_wikidata_client()
            label_client.setQuery(f"""
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?label WHERE {{
                    <{uri}> rdfs:label ?label.
                    FILTER(lang(?label) = "en")
                }} LIMIT 1
            """)
            label_result = label_client.query().convert()
            if label_result["results"]["bindings"]:
                label_val = label_result["results"]["bindings"][0]["label"]["value"]
                if len(label_val) < 50:
                    labels[uri] = label_val
        except Exception as e:
            pass

    data = []
    for item in all_bindings:
        item_uri = item.get("item", {}).get("value")
        creator_uri = item.get("creator", {}).get("value")
        title = labels.get(item_uri, "Unknown")
        author = labels.get(creator_uri, "Necunoscut") if creator_uri else "Necunoscut"
        date_raw = item.get("inception", {}).get("value")
        birthDate_raw = item.get("birthDate", {}).get("value")
        birthPlace_uri = item.get("birthPlace", {}).get("value")
        collection_uri = item.get("collection", {}).get("value")
        location_uri = item.get("location", {}).get("value")
        movement_uri = item.get("movement", {}).get("value")
        creator_movement_uri = item.get("creatorMovement", {}).get("value")
        nationality_uri = item.get("nationality", {}).get("value")

        date = date_raw.split("T")[0] if date_raw else None
        birthDate = birthDate_raw.split("T")[0] if birthDate_raw else None
        birthPlace = labels.get(birthPlace_uri) if birthPlace_uri else None
        museum = labels.get(collection_uri) or labels.get(location_uri) if (collection_uri or location_uri) else None
        movement = labels.get(movement_uri) if movement_uri else None
        creator_movement = labels.get(creator_movement_uri) if creator_movement_uri else None
        nationality = labels.get(nationality_uri) if nationality_uri else None

        data.append({
            "title": title,
            "creator": author,
            "date": date,
            "museum": museum,
            "movement": movement,
            "dbpedia": {
                "birthDate": birthDate,
                "birthPlace": birthPlace,
                "nationality": nationality,
                "movement": creator_movement,
            }
        })

    seen = {}
    for item in data:
        key = (item["title"], item["creator"], item["date"])
        if key not in seen:
            item["movements"] = {item["movement"]} if item["movement"] else set()
            item["museums"] = {item["museum"]} if item["museum"] else set()
            item["creator_movements"] = {item["dbpedia"]["movement"]} if item["dbpedia"]["movement"] else set()
            item["nationalities"] = {item["dbpedia"]["nationality"]} if item["dbpedia"]["nationality"] else set()
            item["birth_dates"] = {item["dbpedia"]["birthDate"]} if item["dbpedia"]["birthDate"] else set()
            item["birth_places"] = {item["dbpedia"]["birthPlace"]} if item["dbpedia"]["birthPlace"] else set()
            seen[key] = item
        else:
            existing = seen[key]
            if item["movement"]:
                existing["movements"].add(item["movement"])
            if item["museum"]:
                existing["museums"].add(item["museum"])
            if item["dbpedia"]["movement"]:
                existing["creator_movements"].add(item["dbpedia"]["movement"])
            if item["dbpedia"]["nationality"]:
                existing["nationalities"].add(item["dbpedia"]["nationality"])
            if item["dbpedia"]["birthDate"]:
                existing["birth_dates"].add(item["dbpedia"]["birthDate"])
            if item["dbpedia"]["birthPlace"]:
                existing["birth_places"].add(item["dbpedia"]["birthPlace"])

    deduped_data = list(seen.values())
    return deduped_data


def query_fuseki(sparql_query: str):
    """Generic Fuseki query function"""
    sparql = SPARQLWrapper(settings.FUSEKI_ENDPOINT)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()