#!/usr/bin/env python
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "provenance.settings")
django.setup()

from django.conf import settings
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper(settings.FUSEKI_ENDPOINT)

# Check what triples exist for Romanian artworks
query = """
PREFIX ex: <http://example.org/ontology/>

SELECT ?predicate ?object WHERE {
    ?art ex:heritage "true" .
    ?art ex:source "data.gov.ro" .
    ?art ?predicate ?object
}
LIMIT 20
"""

sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

print("[DEBUG] Predicates and objects for Romanian artworks:")
print()

for binding in results["results"]["bindings"]:
    pred = binding.get("predicate", {}).get("value", "")
    obj = binding.get("object", {}).get("value", "")
    pred_short = pred.split("/")[-1] if "/" in pred else pred
    print(f"  {pred_short}: {obj[:80]}")
