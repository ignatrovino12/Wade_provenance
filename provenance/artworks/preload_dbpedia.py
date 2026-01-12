from django.conf import settings
from .sparql import get_paintings, EX
from .getty_enrichment import get_getty_enrichment
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
import requests

def artwork_to_rdf(p):
    g = Graph()
    subj = URIRef(EX[p["title"].replace(" ", "_")])

    g.add((subj, RDF.type, EX.Artwork))
    g.add((subj, EX.title, Literal(p["title"])))
    g.add((subj, EX.creator, Literal(p.get("creator"))))
    
    # Add artist URI and Getty ULAN enrichment
    if p.get("creator"):
        creator = p["creator"]
        artist_uri = URIRef(EX[creator.replace(" ", "_")])
        g.add((subj, EX.createdBy, artist_uri))
        g.add((artist_uri, RDF.type, EX.Artist))
        g.add((artist_uri, EX.name, Literal(creator)))
        
        # Add Getty ULAN link for artist
        ulan_data = get_getty_enrichment(creator, "ulan")
        if ulan_data:
            ulan_id = ulan_data.get("ulan_id", "")
            if ulan_id:
                g.add((artist_uri, EX.hasULAN, URIRef(f"http://vocab.getty.edu/page/ulan/{ulan_id}")))
                print(f"[GETTY ULAN] {creator} -> {ulan_id}")
    
    # Handle museum - can be a set or string
    if isinstance(p.get("museum"), set):
        for museum in p["museum"]:
            if museum:
                g.add((subj, EX.museum, Literal(museum)))
    else:
        if p.get("museum"):
            g.add((subj, EX.museum, Literal(p["museum"])))
    
    g.add((subj, EX.date, Literal(p.get("date"))))
    
    # Handle movement - can be a set or string
    if isinstance(p.get("movement"), set):
        for movement in p["movement"]:
            if movement:
                g.add((subj, EX.movement, Literal(movement)))
                # Add Getty AAT link for each movement
                aat_data = get_getty_enrichment(movement, "aat")
                if aat_data:
                    aat_id = aat_data.get("aat_id", "")
                    if aat_id:
                        g.add((subj, EX.hasAAT, URIRef(f"http://vocab.getty.edu/page/aat/{aat_id}")))
                        print(f"[GETTY AAT] {movement} -> {aat_id}")
    else:
        if p.get("movement"):
            g.add((subj, EX.movement, Literal(p["movement"])))
            # Add Getty AAT link for movement
            aat_data = get_getty_enrichment(p["movement"], "aat")
            if aat_data:
                aat_id = aat_data.get("aat_id", "")
                if aat_id:
                    g.add((subj, EX.hasAAT, URIRef(f"http://vocab.getty.edu/page/aat/{aat_id}")))
                    print(f"[GETTY AAT] {p['movement']} -> {aat_id}")

    return g

def send_to_fuseki(graph: Graph, base_endpoint: str | None = None):
    base = base_endpoint or settings.FUSEKI_ENDPOINT.rsplit("/", 1)[0]
    data_endpoint = f"{base}/data"

    data = graph.serialize(format="turtle")
    r = requests.post(
        data_endpoint,
        data=data,
        headers={"Content-Type": "text/turtle"},
    )
    # print("[FUSEKI] status:", r.status_code)

def preload_all(limit=10, total=100):
    print("[PRELOAD] Începem preload RDF în Fuseki...")
    try:
        paintings = get_paintings(limit=limit, total=total)
    except Exception as e:
        print("[PRELOAD ERROR] fetch paintings failed:", e)
        return
    
    print(f"[PRELOAD] Received {len(paintings)} deduplicated artworks from get_paintings()")
    
    for p in paintings:
        # print(f"[RDF] {p['title']}")
        g = artwork_to_rdf(p)
        send_to_fuseki(g)

    print("[PRELOAD] Gata!")
