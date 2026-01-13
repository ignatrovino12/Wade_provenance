import requests
import xml.etree.ElementTree as ET
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
from django.conf import settings
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from .getty_enrichment import get_getty_enrichment

EX = Namespace("http://example.org/ontology/")
CIMO = Namespace("http://www.cidoc-crm.org/cidoc-crm/")


def get_wikidata_artist_details(artist_name):
    """Query Wikidata for artist details (birthDate, birthPlace, nationality, movement)"""
    try:
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        
        escaped_name = artist_name.replace("'", "\\'")
        
        query = f"""
            SELECT ?birthDate ?birthPlaceLabel ?nationalityLabel ?movementLabel WHERE {{
                ?person rdfs:label "{escaped_name}"@en .
                ?person wdt:P31 wd:Q5 .
                OPTIONAL {{ ?person wdt:P569 ?birthDate }}
                OPTIONAL {{ ?person wdt:P19 ?birthPlace . ?birthPlace rdfs:label ?birthPlaceLabel . FILTER(LANG(?birthPlaceLabel) = "en") }}
                OPTIONAL {{ ?person wdt:P27 ?nationality . ?nationality rdfs:label ?nationalityLabel . FILTER(LANG(?nationalityLabel) = "en") }}
                OPTIONAL {{ ?person wdt:P135 ?movement . ?movement rdfs:label ?movementLabel . FILTER(LANG(?movementLabel) = "en") }}
            }}
            LIMIT 1
        """
        
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        
        if results["results"]["bindings"]:
            binding = results["results"]["bindings"][0]
            
            # Safely extract string values
            birth_date = binding.get("birthDate", {}).get("value", "")
            birth_place = binding.get("birthPlaceLabel", {}).get("value", "")
            nationality = binding.get("nationalityLabel", {}).get("value", "")
            movement = binding.get("movementLabel", {}).get("value", "")
            
            return {
                "birthDate": str(birth_date) if birth_date else None,
                "birthPlace": str(birth_place) if birth_place else None,
                "nationality": str(nationality) if nationality else None,
                "movement": str(movement) if movement else None,
            }
    except Exception as e:
        print(f"[ROMANIAN] Wikidata lookup failed for '{artist_name}': {str(e)[:100]}")
    
    return {"birthDate": None, "birthPlace": None, "nationality": None, "movement": None}

def download_romanian_artworks():
    api_url = "https://data.gov.ro/api/3/action/package_show?id=bunuri-culturale-clasate-arta"
    
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Find XML resource
        resources = data.get("result", {}).get("resources", [])
        xml_resource = None
        
        for resource in resources:
            if resource.get("format", "").lower() == "xml":
                xml_resource = resource
                break
        
        if not xml_resource:
            print("[ROMANIAN] No XML resource found")
            return None
        
        download_url = xml_resource.get("url")
        if not download_url:
            print("[ROMANIAN] No download URL found")
            return None
        
        print(f"[ROMANIAN] Downloading from {download_url}...")
        xml_response = requests.get(download_url, timeout=30)
        xml_response.raise_for_status()
        
        return xml_response.content
    except Exception as e:
        print(f"[ROMANIAN ERROR] Failed to download: {e}")
        return None


def parse_romanian_xml(xml_content, limit=1000):
    artworks = []
    max_artworks = limit  # Configurable limit
    debug_count = 0
    
    try:
        root = ET.fromstring(xml_content)
        
        ns = {'lido': 'http://www.lido-schema.org'}
        
        for lido_item in root.findall('lido:lido', ns):
            if len(artworks) >= max_artworks:
                break
                
            artwork = {}
            
            rec_id = lido_item.find('lido:lidoRecID', ns)
            if rec_id is not None:
                artwork["id"] = rec_id.text
            
            desc_meta = lido_item.find('lido:descriptiveMetadata', ns)
            if desc_meta is not None:
                title = None
                
                obj_name = desc_meta.find('.//lido:objectNameWrap/lido:objectName/lido:appellationValue', ns)
                if obj_name is not None and obj_name.text:
                    title = obj_name.text
                
                if not title:
                    title_elem = desc_meta.find('.//lido:titleWrap/lido:titleSet/lido:appellationValue', ns)
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text
                
                if not title:
                    desc_elem = desc_meta.find('.//lido:objectDescriptionWrap/lido:objectDescription/lido:descriptiveNoteValue', ns)
                    if desc_elem is not None and desc_elem.text:
                        title = desc_elem.text[:100]
                
                if not title:
                    obj_classif = desc_meta.find('.//lido:objectClassificationWrap/lido:classificationWrap/lido:classification', ns)
                    if obj_classif is not None and obj_classif.text:
                        title = obj_classif.text
                
                if title:
                    artwork["title"] = title.strip()
                
                actor_elem = desc_meta.find('.//lido:eventWrap/lido:eventSet/lido:event/lido:eventActor/lido:actorInRole/lido:actor/lido:nameActorSet/lido:appellationValue', ns)
                if actor_elem is not None and actor_elem.text:
                    artwork["creator"] = actor_elem.text
                
                if "creator" not in artwork:
                    alt_actor = desc_meta.find('.//lido:actorInRole/lido:actor/lido:nameActorSet/lido:appellationValue', ns)
                    if alt_actor is not None and alt_actor.text:
                        artwork["creator"] = alt_actor.text
                
                date_elem = desc_meta.find('.//lido:eventWrap/lido:eventSet/lido:event/lido:eventDate/lido:displayDate', ns)
                if date_elem is not None and date_elem.text:
                    artwork["date"] = date_elem.text
                
                style_elem = desc_meta.find('.//lido:styleWrap/lido:styleSet/lido:term', ns)
                if style_elem is not None and style_elem.text:
                    artwork["movement"] = style_elem.text.strip()
                
                if "movement" not in artwork:
                    period_elem = desc_meta.find('.//lido:periodWrap/lido:periodSet/lido:term', ns)
                    if period_elem is not None and period_elem.text:
                        artwork["movement"] = period_elem.text.strip()
                
                if "movement" not in artwork:
                    culture_elem = desc_meta.find('.//lido:cultureWrap/lido:cultureSet/lido:term', ns)
                    if culture_elem is not None and culture_elem.text:
                        artwork["movement"] = culture_elem.text.strip()
            
            admin_meta = lido_item.find('lido:administrativeMetadata', ns)
            if admin_meta is not None:
                repo = admin_meta.find('.//lido:repositoryWrap/lido:repositorySet/lido:repositoryName/lido:legalBodyName/lido:appellationValue', ns)
                if repo is not None and repo.text:
                    artwork["museum"] = repo.text.strip()
                
                if "museum" not in artwork:
                    alt_repo = admin_meta.find('.//lido:repositoryName/lido:legalBodyName/lido:appellationValue', ns)
                    if alt_repo is not None and alt_repo.text:
                        artwork["museum"] = alt_repo.text.strip()
                
                if "museum" not in artwork:
                    broad_repo = admin_meta.find('.//lido:repositoryName/lido:appellationValue', ns)
                    if broad_repo is not None and broad_repo.text:
                        artwork["museum"] = broad_repo.text.strip()
                
                if "museum" not in artwork:
                    record_source = admin_meta.find('.//lido:recordSource/lido:legalBodyName/lido:appellationValue', ns)
                    if record_source is not None and record_source.text:
                        artwork["museum"] = record_source.text.strip()
                
                measure = admin_meta.find('.//lido:objectMeasurementsWrap/lido:objectMeasurements/lido:measurementSet/lido:measurementValue', ns)
                if measure is not None and measure.text:
                    artwork["size"] = measure.text
                
                # Extract image URL from resourceWrap
                resource_wrap = admin_meta.find('.//lido:resourceWrap/lido:resourceSet/lido:resourceRepresentation', ns)
                if resource_wrap is not None:
                    link_resource = resource_wrap.find('lido:linkResource', ns)
                    if link_resource is not None and link_resource.text:
                        artwork["image_url"] = link_resource.text.strip()
            
            if artwork.get("creator"):
                if not artwork.get("title"):
                    artwork["title"] = f"Lucrare de {artwork.get('creator', 'autor necunoscut')}"
                
                artworks.append(artwork)
                
                if len(artworks) <= 3:
                    print(f"\n[DEBUG] Artwork {len(artworks)}:")
                    for key, val in artwork.items():
                        try:
                            print(f"  {key}: {val}")
                        except:
                            print(f"  {key}: [encoding error]")
        
        print(f"[ROMANIAN] Parsed {len(artworks)} artworks from LIDO XML (max 1000)")
        if len(artworks) > 0:
            print(f"[ROMANIAN] Sample fields: {list(artworks[0].keys())}")
        return artworks
    
    except ET.ParseError as e:
        print(f"[ROMANIAN ERROR] XML parse failed: {e}")
        return []
    except Exception as e:
        print(f"[ROMANIAN ERROR] Parse error: {e}")
        import traceback
        traceback.print_exc()
        return []


def push_romanian_to_fuseki(artworks):
    """Push Romanian artworks to Fuseki as RDF with enriched artist details"""
    if not artworks:
        print("[ROMANIAN] No artworks to push")
        return
    
    import re
    import os
    
    g = Graph()
    g.bind("ex", EX)
    
    artist_cache = {}
    skip_wikidata = os.getenv("SKIP_WIKIDATA", "false").lower() == "true"
    if skip_wikidata:
        print("[ROMANIAN] SKIP_WIKIDATA=true — skipping Wikidata enrichment")
    
    for idx, artwork in enumerate(artworks):
        try:
            title = str(artwork.get("title", "Unknown"))
            creator = str(artwork.get("creator", "Unknown"))
            date = str(artwork.get("date", "")) if artwork.get("date") else ""
            museum = str(artwork.get("museum", "")) if artwork.get("museum") else ""
            
            # Create URIs with safe names
            title_safe = re.sub(r'[^a-zA-Z0-9_]', '', title[:80])
            creator_safe = re.sub(r'[^a-zA-Z0-9_]', '', creator[:80])
            
            art_uri = URIRef(EX[f"ro_{idx}_{title_safe}"])
            artist_uri = URIRef(EX[f"artist_{creator_safe}_{idx}"])
            
            # Add artwork triples
            g.add((art_uri, RDF.type, EX.Artwork))
            g.add((art_uri, EX.title, Literal(title)))
            g.add((art_uri, EX.creator, Literal(creator)))
            g.add((art_uri, EX.createdBy, artist_uri))
            g.add((art_uri, EX.heritage, Literal("true")))
            g.add((art_uri, EX.source, Literal("data.gov.ro")))
            
            if date:
                g.add((art_uri, EX.date, Literal(date)))
            if museum:
                g.add((art_uri, EX.museum, Literal(museum)))
            
            # Add image URL if available
            if artwork.get("image_url"):
                image_url = str(artwork.get("image_url")).strip()
                if image_url:
                    g.add((art_uri, EX.image, Literal(image_url)))
            
            # If movement extracted from LIDO, add it to artwork as well
            if artwork.get("movement"):
                try:
                    movement_val = str(artwork.get("movement", "")).strip()
                    if movement_val:
                        g.add((art_uri, EX.movement, Literal(movement_val)))
                        
                        # Add Getty AAT link for movement
                        aat_data = get_getty_enrichment(movement_val, "aat")
                        if aat_data:
                            aat_id = aat_data.get("aat_id", "")
                            if aat_id:
                                g.add((art_uri, EX.hasAAT, URIRef(f"http://vocab.getty.edu/page/aat/{aat_id}")))
                                # print(f"[GETTY AAT] {movement_val} -> {aat_id}")
                except Exception as e:
                    print(f"[ROMANIAN] Skipping artwork movement due to error: {str(e)[:100]}")
            
            artist_details = {"birthDate": None, "birthPlace": None, "nationality": None, "movement": None}
            if not skip_wikidata:
                if creator not in artist_cache:
                    print(f"[ROMANIAN] Querying Wikidata for {creator}...")
                    artist_cache[creator] = get_wikidata_artist_details(creator)
                artist_details = artist_cache.get(creator, artist_details)
            
            g.add((artist_uri, RDF.type, EX.Artist))
            g.add((artist_uri, EX.name, Literal(creator)))
            
            ulan_data = get_getty_enrichment(creator, "ulan")
            if ulan_data:
                ulan_id = ulan_data.get("ulan_id", "")
                if ulan_id:
                    g.add((artist_uri, EX.hasULAN, URIRef(f"http://vocab.getty.edu/page/ulan/{ulan_id}")))
                    # print(f"[GETTY ULAN] {creator} -> {ulan_id}")
            
            if artist_details.get("birthDate"):
                birth_date = str(artist_details["birthDate"]).strip()
                if birth_date:
                    g.add((artist_uri, EX.birthDate, Literal(birth_date)))
            
            if artist_details.get("birthPlace"):
                birth_place = str(artist_details["birthPlace"]).strip()
                if birth_place:
                    g.add((artist_uri, EX.birthPlace, Literal(birth_place)))
            
            if artist_details.get("nationality"):
                nationality = str(artist_details["nationality"]).strip()
                if nationality:
                    g.add((artist_uri, EX.nationality, Literal(nationality)))
            
            if artist_details.get("movement"):
                movement = str(artist_details["movement"]).strip()
                if movement:
                    g.add((artist_uri, EX.movement, Literal(movement)))
        
        except Exception as e:
            print(f"[ROMANIAN] Error processing artwork {idx}: {str(e)[:100]}")
            continue
    
    print(f"[ROMANIAN] Pushing {len(g)} triples to Fuseki...")
    batch_size = 100
    batch_count = 0
    
    triples_list = list(g)
    for i in range(0, len(triples_list), batch_size):
        try:
            batch_g = Graph()
            batch_g.bind("ex", EX)
            for triple in triples_list[i:i+batch_size]:
                batch_g.add(triple)
            
            # Serialize to N-Triples
            nt_data = batch_g.serialize(format='nt')
            if isinstance(nt_data, bytes):
                nt_data = nt_data.decode('utf-8')
            
            sparql = SPARQLWrapper(settings.FUSEKI_UPDATE)
            sparql.setMethod(POST)
            
            insert_query = f"INSERT DATA {{ {nt_data} }}"
            
            sparql.setQuery(insert_query)
            sparql.query()
            batch_count += 1
            print(f"[ROMANIAN FUSEKI] Batch {batch_count} pushed ({len(batch_g)} triples)")
        
        except Exception as e:
            err_msg = str(e)[:150]
            print(f"[ROMANIAN FUSEKI ERROR] Batch {batch_count}: {err_msg}")
    
    print(f"[ROMANIAN] Total {len(triples_list)} triples pushed in {batch_count} batches")


def import_romanian_heritage(limit=100):
    print(f"[ROMANIAN] Starting import (limit: {limit} artworks)...")
    
    xml_content = download_romanian_artworks()
    if not xml_content:
        print("[ROMANIAN] Download failed, skipping import")
        return
    
    artworks = parse_romanian_xml(xml_content, limit=limit)
    if not artworks:
        print("[ROMANIAN] No artworks parsed")
        return
    
    push_romanian_to_fuseki(artworks)
    
    print("[ROMANIAN] Import complete!")


def import_romanian_all(total=100):

    import_romanian_heritage(limit=total)
