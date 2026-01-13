# REST API Documentation - Artwork Provenance System

## Overview

This document provides the complete REST API specification for the Artwork Provenance System. The API enables querying artworks from multiple sources (Wikidata, DBpedia, data.gov.ro) with enrichment from Getty vocabularies (ULAN for artists, AAT for movements), stored and queried via Apache Jena Fuseki triple store.

**Base URL:** `http://localhost:8000`

**Authentication:** None required (public API)

**Data Format:** JSON

**CORS:** Enabled

**Current Collection:** 97 artworks with DBpedia enrichment

---

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Data Models](#data-models)
3. [Endpoint Details](#endpoint-details)
4. [Usage Examples](#usage-examples)
5. [Pragmatic Case Studies](#pragmatic-case-studies)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

---

## API Endpoints

### Summary Table

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Artworks list page (HTML) |
| `/api/` | GET | Paginated artworks data (JSON) |
| `/sparql` | GET, POST | SPARQL query endpoint |
| `/stats/` | GET | Statistics page (HTML) |
| `/stats/api/` | GET | Statistics data (JSON) |
| `/getty/stats/` | GET | Getty statistics page (HTML) |
| `/getty/stats/api/` | GET | Getty enrichment statistics (JSON) |
| `/romanian/` | GET | Romanian heritage page (HTML) |
| `/romanian/api/` | GET | Romanian heritage artworks (JSON) |

---

## Data Models

### Artwork Object

```json
{
  "title": "String",
  "creators": ["String"],
  "creator": "String",
  "date": "String",
  "museums": ["String"],
  "museum": "String",
  "movements": ["String"],
  "movement": "String",
  "creator_movements": ["String"],
  "birth_dates": ["String"],
  "birth_places": ["String"],
  "nationalities": ["String"],
  "image_url": "String (URL)",
  "dbpedia": {
    "birthDate": "String",
    "birthPlace": "String",
    "nationality": "String",
    "movement": "String"
  }
}
```

### Paginated Response

```json
{
  "items": [/* Array of Artwork objects */],
  "total": 1234,
  "page": 1,
  "per_page": 50,
  "total_pages": 25
}
```

**Note:** Default `per_page` is **50**. Can be customized via query parameter (e.g., `?per_page=20`).

### Statistics Object

```json
{
  "total_artworks": 97,
  "top_creators": [
    {"creator": "Johannes Vermeer", "count": 5},
    {"creator": "Salvador Dalí", "count": 5},
    {"creator": "Grigorescu, Nicolae", "count": 4}
  ],
  "top_museums": [
    {"museum": "Institutul Național al Patrimoniului", "count": 40},
    {"museum": "Kunsthistorisches Museum", "count": 7},
    {"museum": "Bavarian State Painting Collections", "count": 6}
  ],
  "top_movements": [
    {"movement": "Dutch Golden Age painting", "count": 5},
    {"movement": "Mannerism", "count": 4},
    {"movement": "Baroque", "count": 3}
  ],
  "by_century": [
    {"century": "1500.0s", "count": 16},
    {"century": "1900.0s", "count": 20},
    {"century": "1800.0s", "count": 15}
  ],
  "museum_breakdown": [
    {
      "museum": "Institutul Național al Patrimoniului",
      "total_artworks": 40,
      "top_movements": []
    },
    {
      "museum": "Kunsthistorisches Museum",
      "total_artworks": 7,
      "top_movements": [
        {"movement": "Mannerism", "movement_count": 2},
        {"movement": "German Renaissance", "movement_count": 1}
      ]
    }
  ]
}
```

### Getty Statistics Object

```json
{
  "total_artworks": 1234,
  "getty_aat_artworks": 800,
  "getty_ulan_artists": 650,
  "top_getty_movements": [
    {
      "movement": "String",
      "aat_id": "300021147",
      "aat_url": "http://vocab.getty.edu/page/aat/300021147",
      "count": 123
    }
  ],
  "top_getty_artists": [
    {
      "artist": "String",
      "ulan_id": "500012345",
      "ulan_url": "http://vocab.getty.edu/page/ulan/500012345",
      "count": 123
    }
  ]
}
```

### SPARQL Response

```json
{
  "head": {
    "vars": ["title", "creator"]
  },
  "results": {
    "bindings": [
      {
        "title": {
          "type": "literal",
          "value": "Artwork Title"
        },
        "creator": {
          "type": "literal",
          "value": "Artist Name"
        }
      }
    ]
  }
}
```

---

## Endpoint Details

### 1. Get Artworks (Paginated)

**Endpoint:** `GET /api/`

**Description:** Retrieve paginated list of artworks with enriched metadata from DBpedia.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | Integer | 1 | Page number (1-based) |
| `per_page` | Integer | 50 | Items per page (max: 100) |

**Example Request:**
```bash
# Default per_page=50
curl "http://localhost:8000/api/?page=1"

# Custom per_page
curl "http://localhost:8000/api/?page=1&per_page=20"
```

**Example Response:**
```json
{
  "items": [
    {
      "title": "Venus of Urbino",
      "creators": ["Titian"],
      "creator": "Titian",
      "date": "1538-01-01",
      "museums": ["Uffizi Gallery"],
      "museum": "Uffizi Gallery",
      "movements": ["High Renaissance", "Venetian school"],
      "movement": "High Renaissance",
      "creator_movements": ["High Renaissance", "Venetian school"],
      "birth_dates": ["1490-01-01"],
      "birth_places": ["Pieve di Cadore"],
      "nationalities": ["Republic of Venice"],
      "image_url": "http://commons.wikimedia.org/wiki/Special:FilePath/Tiziano%27s%20Venere%20di%20Urbino.jpg",
      "dbpedia": {
        "birthDate": "1490-01-01",
        "birthPlace": "Pieve di Cadore",
        "nationality": "Republic of Venice",
        "movement": "High Renaissance"
      }
    }
  ],
  "total": 97,
  "page": 1,
  "per_page": 20,
  "total_pages": 5
}
```

**Response Codes:**
- `200 OK` - Success
- `500 Internal Server Error` - SPARQL query failed

---

### 2. SPARQL Endpoint

**Endpoint:** `GET|POST /sparql`

**Description:** Execute custom SPARQL queries against the Fuseki triple store.

**Request Methods:**
- **GET** - Display SPARQL query form (HTML) or execute query with query parameter
- **POST** - Execute SPARQL query (returns JSON, requires CSRF token for browser requests)

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | String | Yes | SPARQL query string |

**Note:** POST requests from browsers require Django CSRF token. For API clients (curl, Postman, programmatic access), use GET method with query parameter, or configure CSRF exemption.

**Example Request (GET with query):**
```bash
curl "http://localhost:8000/sparql?query=PREFIX%20ex%3A%20%3Chttp%3A%2F%2Fexample.org%2Fontology%2F%3E%0ASELECT%20%3Ftitle%20WHERE%20%7B%20%3Fart%20ex%3Atitle%20%3Ftitle%20%7D%20LIMIT%2010"
```

**Example Request (POST):**
```bash
curl -X POST http://localhost:8000/sparql \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "query=PREFIX ex: <http://example.org/ontology/>
SELECT ?title ?creator WHERE {
  ?art ex:title ?title ;
       ex:creator ?creator .
} LIMIT 10"
```

**Example Response:**
```json
{
  "head": {
    "vars": ["title", "creator"]
  },
  "results": {
    "bindings": [
      {
        "title": {
          "type": "literal",
          "value": "Starry Night"
        },
        "creator": {
          "type": "literal",
          "value": "Vincent van Gogh"
        }
      }
    ]
  }
}
```

**Response Codes:**
- `200 OK` - Success
- `405 Method Not Allowed` - Invalid HTTP method
- `500 Internal Server Error` - SPARQL syntax error or Fuseki unavailable

---

### 3. Statistics API

**Endpoint:** `GET /stats/api/`

**Description:** Comprehensive statistics about the artwork collection.

**Query Parameters:** None

**Example Request:**
```bash
curl "http://localhost:8000/stats/api/"
```

**Example Response:**
```json
{
  "total_artworks": 97,
  "top_creators": [
    {"creator": "Johannes Vermeer", "count": 5},
    {"creator": "Salvador Dalí", "count": 5},
    {"creator": "Grigorescu, Nicolae", "count": 4},
    {"creator": "Norman Rockwell", "count": 4},
    {"creator": "Pieter Brueghel the Elder", "count": 4},
    {"creator": "Tonitza, Nicolae", "count": 4}
  ],
  "top_museums": [
    {"museum": "Institutul Național al Patrimoniului", "count": 40},
    {"museum": "Kunsthistorisches Museum", "count": 7},
    {"museum": "Bavarian State Painting Collections", "count": 6},
    {"museum": "Norman Rockwell Museum", "count": 4}
  ],
  "top_movements": [
    {"movement": "Dutch Golden Age painting", "count": 5},
    {"movement": "Mannerism", "count": 4},
    {"movement": "Baroque", "count": 3},
    {"movement": "High Renaissance", "count": 3},
    {"movement": "Romanticism", "count": 3}
  ],
  "by_century": [
    {"century": "200.0s", "count": 1},
    {"century": "1100.0s", "count": 1},
    {"century": "1300.0s", "count": 1},
    {"century": "1400.0s", "count": 3},
    {"century": "1500.0s", "count": 16},
    {"century": "1600.0s", "count": 10},
    {"century": "1700.0s", "count": 2},
    {"century": "1800.0s", "count": 15},
    {"century": "1900.0s", "count": 20},
    {"century": "2000.0s", "count": 1}
  ],
  "museum_breakdown": [
    {
      "museum": "Institutul Național al Patrimoniului",
      "total_artworks": 40,
      "top_movements": []
    },
    {
      "museum": "Kunsthistorisches Museum",
      "total_artworks": 7,
      "top_movements": [
        {"movement": "Mannerism", "movement_count": 2},
        {"movement": "German Renaissance", "movement_count": 1},
        {"movement": "High Renaissance", "movement_count": 1}
      ]
    },
    {
      "museum": "Bavarian State Painting Collections",
      "total_artworks": 6,
      "top_movements": [
        {"movement": "Baroque", "movement_count": 1},
        {"movement": "Early Netherlandish painting", "movement_count": 1},
        {"movement": "High Renaissance", "movement_count": 1}
      ]
    }
  ]
}
```

**Statistics Breakdown:**

1. **total_artworks** - Total count of artworks in database
2. **top_creators** - Top 10 artists by artwork count
3. **top_museums** - Top 10 museums by artwork count (excludes null/None)
4. **top_movements** - Top 10 art movements (excludes null/None)
5. **by_century** - Artwork distribution by century (parsed from dates)
6. **museum_breakdown** - For each museum: total artworks + top 5 movements

**Response Codes:**
- `200 OK` - Success
- `500 Internal Server Error` - SPARQL query failed

---

### 4. Getty Statistics API

**Endpoint:** `GET /getty/stats/api/`

**Description:** Statistics about Getty vocabulary enrichment (ULAN for artists, AAT for movements).

**Query Parameters:** None

**Example Request:**
```bash
curl "http://localhost:8000/getty/stats/api/"
```

**Example Response:**
```json
{
  "total_artworks": 97,
  "getty_aat_artworks": 36,
  "getty_ulan_artists": 38,
  "top_getty_movements": [
    {
      "movement": "High Renaissance",
      "aat_id": "300021142",
      "aat_url": "http://vocab.getty.edu/page/aat/300021142",
      "count": 6
    },
    {
      "movement": "German Renaissance",
      "aat_id": "300103380",
      "aat_url": "http://vocab.getty.edu/page/aat/300103380",
      "count": 5
    },
    {
      "movement": "Baroque",
      "aat_id": "300021034",
      "aat_url": "http://vocab.getty.edu/page/aat/300021034",
      "count": 4
    }
  ],
  "top_getty_artists": [
    {
      "artist": "Johannes Vermeer",
      "ulan_id": "500032927",
      "ulan_url": "http://vocab.getty.edu/page/ulan/500032927",
      "count": 5
    },
    {
      "artist": "Salvador Dalí",
      "ulan_id": "500009365",
      "ulan_url": "http://vocab.getty.edu/page/ulan/500009365",
      "count": 5
    },
    {
      "artist": "Tonitza, Nicolae",
      "ulan_id": "500013832",
      "ulan_url": "http://vocab.getty.edu/page/ulan/500013832",
      "count": 4
    }
  ]
}
```

**Vocabulary Types:**
- **AAT (Art & Architecture Thesaurus)** - Standardized art movement terms
- **ULAN (Union List of Artist Names)** - Standardized artist identifiers

**Response Codes:**
- `200 OK` - Success
- `500 Internal Server Error` - Query or enrichment failed

---

### 5. Romanian Heritage API

**Endpoint:** `GET /romanian/api/`

**Description:** Retrieve artworks from Romanian cultural heritage (data.gov.ro source).

**Query Parameters:** None

**Example Request:**
```bash
curl "http://localhost:8000/romanian/api/"
```

**Example Response:**
```json
[
  {
    "title": "Peasant Woman from Muscel",
    "creators": ["Nicolae Grigorescu"],
    "creator": "Nicolae Grigorescu",
    "date": "1870",
    "museums": ["National Museum of Art of Romania"],
    "museum": "National Museum of Art of Romania",
    "movements": ["Realism"],
    "movement": "Realism",
    "creator_movements": ["Romanian Realism"],
    "birth_dates": ["1838-05-15"],
    "birth_places": ["Pitaru"],
    "nationalities": ["Romanian"],
    "image_url": "http://example.com/image.jpg",
    "dbpedia": {
      "birthDate": "1838-05-15",
      "birthPlace": "Pitaru",
      "nationality": "Romanian",
      "movement": "Romanian Realism"
    }
  }
]
```

**Filtering:**
- Automatically filters artworks with `ex:heritage "true"`
- Automatically filters artworks with `ex:source "data.gov.ro"`

**Response Codes:**
- `200 OK` - Success
- `500 Internal Server Error` - SPARQL query failed


---

## Usage Examples

### Example 1: Fetching Artworks with JavaScript/Fetch

```javascript
async function fetchArtworks(page = 1, perPage = 50) {
  const response = await fetch(
    `http://localhost:8000/api/?page=${page}&per_page=${perPage}`
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const data = await response.json();
  return data;
}

// Usage
const artworkData = await fetchArtworks(1, 50); // or fetchArtworks(1, 20) for 20 items
console.log(`Total artworks: ${artworkData.total}`);
console.log(`Current page: ${artworkData.page} of ${artworkData.total_pages}`);

artworkData.items.forEach(artwork => {
  console.log(`${artwork.title} by ${artwork.creator}`);
});
```

### Example 2: Executing SPARQL Query

```javascript
async function executeSPARQL(query) {
  // Using GET method to avoid CSRF issues
  const url = new URL('http://localhost:8000/sparql');
  url.searchParams.append('query', query);
  
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`SPARQL error! status: ${response.status}`);
  }
  
  const data = await response.json();
  return data;
}

// Usage - Find all Baroque artworks
const query = `
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?title ?creator ?date WHERE {
  ?art rdf:type ex:Artwork ;
       ex:title ?title ;
       ex:creator ?creator ;
       ex:movement "Baroque" .
  OPTIONAL { ?art ex:date ?date }
}
ORDER BY ?date
LIMIT 50
`;

const results = await executeSPARQL(query);
console.log(`Found ${results.results.bindings.length} Baroque artworks`);

results.results.bindings.forEach(binding => {
  console.log(`${binding.title.value} - ${binding.creator.value} (${binding.date?.value || 'Unknown'})`);
});
```

### Example 3: Loading Statistics Dashboard

```javascript
async function loadStatistics() {
  const response = await fetch('http://localhost:8000/stats/api/');
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const stats = await response.json();
  return stats;
}

// Usage with Chart.js or similar
const stats = await loadStatistics();

console.log(`Total artworks in collection: ${stats.total_artworks}`);

// Display top creators
console.log('\nTop 5 Artists:');
stats.top_creators.slice(0, 5).forEach((creator, index) => {
  console.log(`${index + 1}. ${creator.creator}: ${creator.count} artworks`);
});

// Display century distribution
console.log('\nArtworks by Century:');
stats.by_century.forEach(century => {
  console.log(`${century.century}: ${century.count} artworks`);
});

// Prepare data for charts
const chartData = {
  movements: {
    labels: stats.top_movements.map(m => m.movement),
    data: stats.top_movements.map(m => m.count)
  },
  museums: {
    labels: stats.top_museums.map(m => m.museum),
    data: stats.top_museums.map(m => m.count)
  }
};
```

### Example 4: Romanian Heritage Collection

```javascript
async function loadRomanianHeritage() {
  const response = await fetch('http://localhost:8000/romanian/api/');
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const artworks = await response.json();
  return artworks;
}

// Usage - Display Romanian cultural heritage
const romanianArt = await loadRomanianHeritage();
console.log(`Romanian heritage collection: ${romanianArt.length} artworks\n`);

// Group by museum
const byMuseum = {};
romanianArt.forEach(artwork => {
  const museum = artwork.museum || 'Unknown';
  if (!byMuseum[museum]) {
    byMuseum[museum] = [];
  }
  byMuseum[museum].push(artwork);
});

Object.entries(byMuseum).forEach(([museum, artworks]) => {
  console.log(`\n${museum}: ${artworks.length} artworks`);
  artworks.slice(0, 3).forEach(art => {
    console.log(`  - ${art.title} by ${art.creator}`);
  });
});
```

### Example 5: Getty Vocabulary Integration Analysis

```javascript
async function analyzeGettyIntegration() {
  const response = await fetch('http://localhost:8000/getty/stats/api/');
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const getty = await response.json();
  return getty;
}

// Usage - Calculate enrichment coverage
const getty = await analyzeGettyIntegration();

const aatCoverage = (getty.getty_aat_artworks / getty.total_artworks * 100).toFixed(2);
const ulanArtistsTotal = getty.top_getty_artists.reduce((sum, a) => sum + a.count, 0);

console.log('Getty Vocabulary Integration Report');
console.log('====================================\n');
console.log(`Total Artworks: ${getty.total_artworks}`);
console.log(`AAT Enriched Artworks: ${getty.getty_aat_artworks} (${aatCoverage}%)`);
console.log(`ULAN Enriched Artists: ${getty.getty_ulan_artists}`);

console.log('\nTop Getty AAT Movements:');
getty.top_getty_movements.slice(0, 5).forEach((movement, index) => {
  console.log(`${index + 1}. ${movement.movement}`);
  console.log(`   AAT ID: ${movement.aat_id}`);
  console.log(`   URL: ${movement.aat_url}`);
  console.log(`   Artworks: ${movement.count}\n`);
});

console.log('Top Getty ULAN Artists:');
getty.top_getty_artists.slice(0, 5).forEach((artist, index) => {
  console.log(`${index + 1}. ${artist.artist}`);
  console.log(`   ULAN ID: ${artist.ulan_id}`);
  console.log(`   URL: ${artist.ulan_url}`);
  console.log(`   Artworks: ${artist.count}\n`);
});
```

### Example 6: Pagination with Infinite Scroll

```javascript
class ArtworkLoader {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.currentPage = 0;
    this.perPage = 24;
    this.hasMore = true;
    this.allArtworks = [];
  }
  
  async loadNextPage() {
    if (!this.hasMore) {
      console.log('No more artworks to load');
      return [];
    }
    
    this.currentPage++;
    const url = `${this.baseUrl}/api/?page=${this.currentPage}&per_page=${this.perPage}`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    this.allArtworks.push(...data.items);
    this.hasMore = this.currentPage < data.total_pages;
    
    return data.items;
  }
  
  async loadAll() {
    while (this.hasMore) {
      await this.loadNextPage();
      // Add delay to avoid overwhelming the server
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    return this.allArtworks;
  }
}

// Usage
const loader = new ArtworkLoader();

// Load next page on scroll
window.addEventListener('scroll', async () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
    const newArtworks = await loader.loadNextPage();
    displayArtworks(newArtworks); // Your display function
  }
});

// Or load all at once
const allArtworks = await loader.loadAll();
console.log(`Loaded ${allArtworks.length} artworks total`);
```

### Example 7: Python Integration

```python
import requests

class ProvenanceAPI:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
    
    def get_artworks(self, page=1, per_page=50):
        """Fetch paginated artworks (default per_page=50)"""
        url = f"{self.base_url}/api/"
        params = {'page': page, 'per_page': per_page}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def sparql_query(self, query):
        """Execute SPARQL query using GET to avoid CSRF issues"""
        url = f"{self.base_url}/sparql"
        params = {'query': query}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_statistics(self):
        """Get collection statistics"""
        url = f"{self.base_url}/stats/api/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_getty_statistics(self):
        """Get Getty vocabulary statistics"""
        url = f"{self.base_url}/getty/stats/api/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_romanian_heritage(self):
        """Get Romanian heritage artworks"""
        url = f"{self.base_url}/romanian/api/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# Usage
api = ProvenanceAPI()

# Fetch first page of artworks (using default 50 items)
artworks = api.get_artworks(page=1)
print(f"Total artworks: {artworks['total']}")

# Or specify custom page size
artworks = api.get_artworks(page=1, per_page=20)
print(f"Fetched {len(artworks['items'])} items")

# Execute SPARQL query
query = """
PREFIX ex: <http://example.org/ontology/>
SELECT ?creator (COUNT(?art) as ?count) WHERE {
    ?art ex:creator ?creator .
}
GROUP BY ?creator
ORDER BY DESC(?count)
LIMIT 10
"""
results = api.sparql_query(query)

# Get statistics
stats = api.get_statistics()
print(f"\nCollection Statistics:")
print(f"Total: {stats['total_artworks']}")
print(f"Top creator: {stats['top_creators'][0]['creator']}")
```

### Example 8: Advanced SPARQL - Find Artists with Multiple Movements

```javascript
async function findArtistsWithMultipleMovements() {
  const query = `
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?creator (GROUP_CONCAT(DISTINCT ?movement; separator=", ") AS ?movements) (COUNT(DISTINCT ?movement) as ?movementCount)
WHERE {
  ?art rdf:type ex:Artwork ;
       ex:creator ?creator ;
       ex:movement ?movement .
  FILTER(?movement != "" && ?movement != "None")
}
GROUP BY ?creator
HAVING (COUNT(DISTINCT ?movement) > 1)
ORDER BY DESC(?movementCount)
LIMIT 20
`;

  // Using GET method to avoid CSRF issues
  const url = new URL('http://localhost:8000/sparql');
  url.searchParams.append('query', query);
  
  const response = await fetch(url);
  
  const data = await response.json();
  
  console.log('Artists spanning multiple movements:\n');
  data.results.bindings.forEach(binding => {
    console.log(`${binding.creator.value}:`);
    console.log(`  Movements: ${binding.movements.value}`);
    console.log(`  Count: ${binding.movementCount.value}\n`);
  });
}
```

---

## Pragmatic Case Studies


### Case Study 1: Romanian Cultural Heritage Portal

**Objective:** Create a dedicated portal showcasing Romanian cultural heritage artworks with enriched metadata.

**Requirements:**
- Display Romanian heritage artworks from data.gov.ro
- Enrich with DBpedia artist information
- Provide statistics on Romanian artists and collections
- Interactive filtering by museum and creator

**Implementation:**

```javascript
// 1. Load Romanian Heritage Collection
async function loadRomanianPortal() {
  const [artworks, stats] = await Promise.all([
    fetch('http://localhost:8000/romanian/api/').then(r => r.json()),
    fetch('http://localhost:8000/stats/api/').then(r => r.json())
  ]);
  
  // Find Institutul Național al Patrimoniului in statistics
  const romanianMuseum = stats.museum_breakdown.find(m =>
    m.museum === 'Institutul Național al Patrimoniului'
  );
  
  return { artworks, romanianMuseum };
}

// 2. Group artworks by creator
function analyzeRomanianArtists(artworks) {
  const artistStats = {};
  
  artworks.forEach(artwork => {
    const creator = artwork.creator;
    if (!artistStats[creator]) {
      artistStats[creator] = {
        name: creator,
        artworks: [],
        birthDate: artwork.dbpedia?.birthDate,
        birthPlace: artwork.dbpedia?.birthPlace,
        nationality: artwork.dbpedia?.nationality
      };
    }
    artistStats[creator].artworks.push(artwork);
  });
  
  return Object.values(artistStats)
    .sort((a, b) => b.artworks.length - a.artworks.length);
}

// 3. Display portal
async function displayRomanianPortal() {
  const { artworks, romanianMuseum } = await loadRomanianPortal();
  const artists = analyzeRomanianArtists(artworks);
  
  console.log('Romanian Cultural Heritage Portal');
  console.log('==================================\n');
  console.log(`Total Romanian Heritage Artworks: ${artworks.length}\n`);
  
  console.log('Collection Source:');
  console.log(`Museum: ${romanianMuseum.museum}`);
  console.log(`Total artworks: ${romanianMuseum.total_artworks}`);
  console.log(`Movements represented: ${romanianMuseum.top_movements.length}\n`);
  
  console.log('Top Romanian Artists:');
  artists.slice(0, 5).forEach((artist, i) => {
    console.log(`${i + 1}. ${artist.name}`);
    console.log(`   Artworks: ${artist.artworks.length}`);
    if (artist.birthDate || artist.birthPlace) {
      console.log(`   Born: ${artist.birthDate || 'Unknown'}, ${artist.birthPlace || 'Unknown'}`);
    }
    console.log(`   Notable works: ${artist.artworks.slice(0, 3).map(a => a.title).join(', ')}\n`);
  });
  
  return { artworks, artists, romanianMuseum };
}

// Usage
const portal = await displayRomanianPortal();
```

**Example Output:**
```
Romanian Cultural Heritage Portal
==================================

Total Romanian Heritage Artworks: 40

Collection Source:
Museum: Institutul Național al Patrimoniului
Total artworks: 40
Movements represented: 0

Top Romanian Artists:
1. Grigorescu, Nicolae
   Artworks: 4
   Notable works: Portret de țărăncuță, Femeie din Muscel, Pădurea de la Barbizon

2. Tonitza, Nicolae
   Artworks: 4
   Notable works: Fetița acrobatului, Portret de țărancă, Bunică cu nepoțel

3. Preziosi, Amedeo
   Artworks: 3
   Notable works: Derviș cerșetor, Procesiune la Balat, Vânzătoare de zarzavat
```

**Outcome:** Comprehensive portal with 40 Romanian heritage artworks from Institutul Național al Patrimoniului, enriched with biographical data and organized by artists.

---

### Case Study 2: Art Movement Timeline Visualization

**Objective:** Create an interactive timeline showing the evolution of art movements with representative artworks.

**Requirements:**
- Organize artworks by century and movement
- Show statistical distribution across time periods
- Link movements to Getty AAT
- Display representative works for each period

**Implementation:**

```javascript
// 1. Fetch data for timeline
async function buildArtMovementTimeline() {
  const [stats, gettyStats] = await Promise.all([
    fetch('http://localhost:8000/stats/api/').then(r => r.json()),
    fetch('http://localhost:8000/getty/stats/api/').then(r => r.json())
  ]);
  
  // Execute SPARQL query to get artworks with dates and movements
  const sparqlQuery = `
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?title ?creator ?date ?movement ?museum WHERE {
  ?art rdf:type ex:Artwork ;
       ex:title ?title ;
       ex:creator ?creator ;
       ex:date ?date ;
       ex:movement ?movement .
  OPTIONAL { ?art ex:museum ?museum }
  FILTER(STRLEN(STR(?date)) >= 4)
  FILTER(REGEX(STR(?date), "^[0-9]{4}"))
  FILTER(?movement != "" && ?movement != "None")
}
ORDER BY ?date
  `;
  
  // Using GET method to avoid CSRF issues
  const url = new URL('http://localhost:8000/sparql');
  url.searchParams.append('query', sparqlQuery);
  const response = await fetch(url);
  
  const sparqlResults = await response.json();
  
  // Organize by century and movement
  const timeline = {};
  
  sparqlResults.results.bindings.forEach(binding => {
    const year = parseInt(binding.date.value.substring(0, 4));
    const century = Math.floor(year / 100) * 100;
    const movement = binding.movement.value;
    
    if (!timeline[century]) {
      timeline[century] = { movements: {}, totalArtworks: 0 };
    }
    
    if (!timeline[century].movements[movement]) {
      timeline[century].movements[movement] = {
        name: movement,
        artworks: [],
        aatInfo: gettyStats.top_getty_movements.find(m => m.movement === movement)
      };
    }
    
    timeline[century].movements[movement].artworks.push({
      title: binding.title.value,
      creator: binding.creator.value,
      date: binding.date.value,
      museum: binding.museum?.value
    });
    
    timeline[century].totalArtworks++;
  });
  
  return { timeline, stats, gettyStats };
}

// 2. Display timeline
async function displayTimeline() {
  const { timeline, stats } = await buildArtMovementTimeline();
  
  console.log('Art Movement Timeline');
  console.log('=====================\n');
  
  const centuries = Object.keys(timeline).sort((a, b) => a - b);
  
  centuries.forEach(century => {
    console.log(`\n${century}s (${timeline[century].totalArtworks} artworks)`);
    console.log('─'.repeat(50));
    
    const movements = Object.values(timeline[century].movements)
      .sort((a, b) => b.artworks.length - a.artworks.length);
    
    movements.forEach(movement => {
      console.log(`\n  ${movement.name} (${movement.artworks.length} artworks)`);
      
      if (movement.aatInfo) {
        console.log(`  Getty AAT: ${movement.aatInfo.aat_url}`);
      }
      
      // Show top 3 artworks
      console.log('  Representative works:');
      movement.artworks.slice(0, 3).forEach(art => {
        console.log(`    • ${art.title} by ${art.creator} (${art.date})`);
      });
    });
  });
  
  // Summary
  console.log('\n\nTimeline Summary:');
  console.log(`Centuries covered: ${centuries.length}`);
  console.log(`First century: ${centuries[0]}s`);
  console.log(`Last century: ${centuries[centuries.length - 1]}s`);
  console.log(`Total artworks: ${Object.values(timeline).reduce((sum, c) => sum + c.totalArtworks, 0)}`);
}

// Usage
await displayTimeline();
```

**Example Output:**
```
Art Movement Timeline
=====================

1500s (16 artworks)
──────────────────────────────────────────────────

  High Renaissance (3 artworks)
  Getty AAT: http://vocab.getty.edu/page/aat/300021142
  Representative works:
    • Venus of Urbino by Tiziano (1538)
    • Madonna of the Pinks by Raffaello Sanzio da Urbino (1506-1507)
    • The Sleeping Venus by Giorgione (1510)

  Mannerism (2 artworks)
  Getty AAT: http://vocab.getty.edu/page/aat/300021140
  Representative works:
    • The Wedding at Cana by Paolo Veronese (1563)
    • Judith and Holofernes by Lucas Cranach the Elder (1530)

1600s (10 artworks)
──────────────────────────────────────────────────

  Dutch Golden Age painting (5 artworks)
  Representative works:
    • Girl with a Pearl Earring by Johannes Vermeer (1665)
    • The Milkmaid by Johannes Vermeer (1658)
    • The Art of Painting by Johannes Vermeer (1666)


Timeline Summary:
Centuries covered: 10
First century: 200s
Last century: 2000s
Total artworks: 70
```

**Outcome:** Interactive timeline spanning multiple centuries with art movements, Getty AAT links, and representative artworks for each period.

---

### Case Study 3: Museum Collection Comparison Tool

**Objective:** Compare collections across multiple museums to identify unique strengths and gaps.

**Requirements:**
- Compare movement distribution across museums
- Identify unique and shared artists
- Calculate collection diversity scores
- Provide actionable insights for curators

**Implementation:**

```javascript
// 1. Fetch detailed museum data via SPARQL
async function fetchMuseumData(museumName) {
  const query = `
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?title ?creator ?movement ?date WHERE {
  ?art rdf:type ex:Artwork ;
       ex:museum "${museumName}" .
  OPTIONAL { ?art ex:title ?title }
  OPTIONAL { ?art ex:creator ?creator }
  OPTIONAL { ?art ex:movement ?movement }
  OPTIONAL { ?art ex:date ?date }
}
  `;
  
  // Using GET method to avoid CSRF issues
  const url = new URL('http://localhost:8000/sparql');
  url.searchParams.append('query', query);
  const response = await fetch(url);
  
  const data = await response.json();
  return data.results.bindings;
}

// 2. Compare two museums
async function compareMuseums(museum1Name, museum2Name) {
  const [m1Artworks, m2Artworks, stats] = await Promise.all([
    fetchMuseumData(museum1Name),
    fetchMuseumData(museum2Name),
    fetch('http://localhost:8000/stats/api/').then(r => r.json())
  ]);
  
  // Extract artists and movements
  const m1Artists = new Set(m1Artworks.map(a => a.creator?.value).filter(Boolean));
  const m2Artists = new Set(m2Artworks.map(a => a.creator?.value).filter(Boolean));
  
  const m1Movements = {};
  const m2Movements = {};
  
  m1Artworks.forEach(a => {
    const mov = a.movement?.value;
    if (mov) m1Movements[mov] = (m1Movements[mov] || 0) + 1;
  });
  
  m2Artworks.forEach(a => {
    const mov = a.movement?.value;
    if (mov) m2Movements[mov] = (m2Movements[mov] || 0) + 1;
  });
  
  // Find shared and unique artists
  const sharedArtists = [...m1Artists].filter(a => m2Artists.has(a));
  const uniqueToM1 = [...m1Artists].filter(a => !m2Artists.has(a));
  const uniqueToM2 = [...m2Artists].filter(a => !m1Artists.has(a));
  
  // Calculate diversity (Shannon entropy)
  const calculateDiversity = (movements) => {
    const total = Object.values(movements).reduce((sum, count) => sum + count, 0);
    return -Object.values(movements).reduce((entropy, count) => {
      const p = count / total;
      return entropy + (p > 0 ? p * Math.log2(p) : 0);
    }, 0);
  };
  
  const comparison = {
    museum1: {
      name: museum1Name,
      artworkCount: m1Artworks.length,
      uniqueArtists: uniqueToM1.length,
      totalArtists: m1Artists.size,
      movements: Object.keys(m1Movements).length,
      diversity: calculateDiversity(m1Movements),
      topMovements: Object.entries(m1Movements)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([mov, count]) => ({ movement: mov, count }))
    },
    museum2: {
      name: museum2Name,
      artworkCount: m2Artworks.length,
      uniqueArtists: uniqueToM2.length,
      totalArtists: m2Artists.size,
      movements: Object.keys(m2Movements).length,
      diversity: calculateDiversity(m2Movements),
      topMovements: Object.entries(m2Movements)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([mov, count]) => ({ movement: mov, count }))
    },
    shared: {
      artists: sharedArtists.length,
      artistNames: sharedArtists.slice(0, 10)
    }
  };
  
  return comparison;
}

// 3. Display comparison
async function displayMuseumComparison(museum1, museum2) {
  console.log('Museum Collection Comparison');
  console.log('============================\n');
  
  const comp = await compareMuseums(museum1, museum2);
  
  console.log(`${comp.museum1.name}:`);
  console.log(`  Artworks: ${comp.museum1.artworkCount}`);
  console.log(`  Total Artists: ${comp.museum1.totalArtists}`);
  console.log(`  Unique Artists: ${comp.museum1.uniqueArtists}`);
  console.log(`  Movements: ${comp.museum1.movements}`);
  console.log(`  Diversity Score: ${comp.museum1.diversity.toFixed(2)}`);
  console.log(`  Top Movements:`);
  comp.museum1.topMovements.forEach(m => {
    console.log(`    - ${m.movement}: ${m.count}`);
  });
  
  console.log(`\n${comp.museum2.name}:`);
  console.log(`  Artworks: ${comp.museum2.artworkCount}`);
  console.log(`  Total Artists: ${comp.museum2.totalArtists}`);
  console.log(`  Unique Artists: ${comp.museum2.uniqueArtists}`);
  console.log(`  Movements: ${comp.museum2.movements}`);
  console.log(`  Diversity Score: ${comp.museum2.diversity.toFixed(2)}`);
  console.log(`  Top Movements:`);
  comp.museum2.topMovements.forEach(m => {
    console.log(`    - ${m.movement}: ${m.count}`);
  });
  
  console.log(`\nShared Collection:`);
  console.log(`  Shared Artists: ${comp.shared.artists}`);
  console.log(`  Example Artists: ${comp.shared.artistNames.slice(0, 5).join(', ')}`);
  
  console.log(`\nInsights:`);
  if (comp.museum1.diversity > comp.museum2.diversity) {
    console.log(`  ${comp.museum1.name} has more diverse collection`);
  } else {
    console.log(`  ${comp.museum2.name} has more diverse collection`);
  }
  
  return comp;
}

// Usage - Compare two real museums from the collection
const comparison = await displayMuseumComparison(
  'Kunsthistorisches Museum',
  'Bavarian State Painting Collections'
);
```

**Example Output:**
```
Museum Collection Comparison
============================

Kunsthistorisches Museum:
  Artworks: 7
  Total Artists: 6
  Unique Artists: 5
  Movements: 4
  Diversity Score: 1.84
  Top Movements:
    - Mannerism: 2
    - German Renaissance: 1
    - High Renaissance: 1
    - Northern Renaissance: 1

Bavarian State Painting Collections:
  Artworks: 6
  Total Artists: 5
  Unique Artists: 4
  Movements: 4
  Diversity Score: 1.92
  Top Movements:
    - Baroque: 1
    - Early Netherlandish painting: 1
    - High Renaissance: 1
    - Italian Renaissance: 1

Shared Collection:
  Shared Artists: 1
  Example Artists: Albrecht Dürer

Insights:
  Bavarian State Painting Collections has more diverse collection
```

**Outcome:** Detailed comparison revealing collection strengths, diversity metrics, and strategic recommendations for curators.

---

### Case Study 4: Getty Vocabulary Coverage Report

**Objective:** Monitor and improve Getty vocabulary integration across the collection.

**Requirements:**
- Track AAT and ULAN coverage percentages
- Identify gaps in vocabulary linking
- Prioritize entities for enrichment
- Generate quality metrics

**Implementation:**

```javascript
// 1. Comprehensive Getty analysis
async function analyzeGettyVocabulary() {
  const [gettyStats, generalStats] = await Promise.all([
    fetch('http://localhost:8000/getty/stats/api/').then(r => r.json()),
    fetch('http://localhost:8000/stats/api/').then(r => r.json())
  ]);
  
  // Calculate coverage percentages
  const aatCoverage = (gettyStats.getty_aat_artworks / gettyStats.total_artworks * 100).toFixed(2);
  const ulanCoverage = (gettyStats.getty_ulan_artists / gettyStats.total_artworks * 100).toFixed(2);
  
  // Identify gaps
  const movementsWithoutAAT = generalStats.top_movements
    .filter(m => !gettyStats.top_getty_movements
      .find(gm => gm.movement === m.movement))
    .map(m => ({ movement: m.movement, artworkCount: m.count }))
    .sort((a, b) => b.artworkCount - a.artworkCount);
  
  const artistsWithoutULAN = generalStats.top_creators
    .filter(c => !gettyStats.top_getty_artists
      .find(ga => ga.artist === c.creator))
    .map(c => ({ artist: c.creator, artworkCount: c.count }))
    .sort((a, b) => b.artworkCount - a.artworkCount);
  
  // Calculate potential impact
  const potentialAATImpact = movementsWithoutAAT
    .slice(0, 10)
    .reduce((sum, m) => sum + m.artworkCount, 0);
  
  const potentialULANImpact = artistsWithoutULAN
    .slice(0, 10)
    .reduce((sum, a) => sum + a.artworkCount, 0);
  
  return {
    coverage: {
      aat: aatCoverage,
      ulan: ulanCoverage,
      overall: ((parseFloat(aatCoverage) + parseFloat(ulanCoverage)) / 2).toFixed(2)
    },
    enriched: {
      aatArtworks: gettyStats.getty_aat_artworks,
      ulanArtists: gettyStats.getty_ulan_artists,
      movements: gettyStats.top_getty_movements.length,
      artists: gettyStats.top_getty_artists.length
    },
    gaps: {
      movementsWithoutAAT,
      artistsWithoutULAN,
      potentialAATImpact,
      potentialULANImpact
    },
    topEnriched: {
      movements: gettyStats.top_getty_movements.slice(0, 10),
      artists: gettyStats.top_getty_artists.slice(0, 10)
    }
  };
}

// 2. Generate report
async function generateGettyReport() {
  console.log('Getty Vocabulary Integration Report');
  console.log('=====================================\n');
  
  const analysis = await analyzeGettyVocabulary();
  
  console.log('Coverage Metrics:');
  console.log(`  AAT Coverage: ${analysis.coverage.aat}%`);
  console.log(`  ULAN Coverage: ${analysis.coverage.ulan}%`);
  console.log(`  Overall Quality Score: ${analysis.coverage.overall}%\n`);
  
  console.log('Currently Enriched:');
  console.log(`  AAT-linked Artworks: ${analysis.enriched.aatArtworks}`);
  console.log(`  ULAN-linked Artists: ${analysis.enriched.ulanArtists}`);
  console.log(`  Movements with AAT: ${analysis.enriched.movements}`);
  console.log(`  Artists with ULAN: ${analysis.enriched.artists}\n`);
  
  console.log('Top Enrichment Gaps (AAT - Movements):');
  analysis.gaps.movementsWithoutAAT.slice(0, 10).forEach((m, i) => {
    console.log(`  ${i + 1}. ${m.movement} (${m.artworkCount} artworks)`);
  });
  console.log(`  Potential impact: ${analysis.gaps.potentialAATImpact} artworks\n`);
  
  console.log('Top Enrichment Gaps (ULAN - Artists):');
  analysis.gaps.artistsWithoutULAN.slice(0, 10).forEach((a, i) => {
    console.log(`  ${i + 1}. ${a.artist} (${a.artworkCount} artworks)`);
  });
  console.log(`  Potential impact: ${analysis.gaps.potentialULANImpact} artworks\n`);
  
  console.log('Recommendations:');
  console.log(`  1. Prioritize enriching top ${Math.min(10, analysis.gaps.movementsWithoutAAT.length)} movements - will cover ${analysis.gaps.potentialAATImpact} artworks`);
  console.log(`  2. Add ULAN for top ${Math.min(10, analysis.gaps.artistsWithoutULAN.length)} artists - will cover ${analysis.gaps.potentialULANImpact} artworks`);
  console.log(`  3. Focus on high-frequency entities for maximum impact`);
  console.log(`  4. Target coverage goal: 80%+ for AAT and ULAN\n`);
  
  return analysis;
}

// Usage
const report = await generateGettyReport();

// Export as JSON for further processing
console.log('\nExporting detailed report...');
const reportJSON = JSON.stringify(report, null, 2);
// Save or send reportJSON
```

**Example Output:**
```
Getty Vocabulary Integration Report
=====================================

Coverage Metrics:
  AAT Coverage: 37.11%
  ULAN Coverage: 39.18%
  Overall Quality Score: 38.14%

Currently Enriched:
  AAT-linked Artworks: 36
  ULAN-linked Artists: 38
  Movements with AAT: 12
  Artists with ULAN: 25

Top Enrichment Gaps (AAT - Movements):
  1. Dutch Golden Age painting (5 artworks)
  2. Post-impressionism (2 artworks)
  3. Pre-Raphaelite Brotherhood (2 artworks)
  Potential impact: 9 artworks

Top Enrichment Gaps (ULAN - Artists):
  1. Norman Rockwell (4 artworks)
  2. Pieter Brueghel the Elder (4 artworks)
  3. Necunoscut (3 artworks)
  Potential impact: 11 artworks

Recommendations:
  1. Prioritize enriching top 3 movements - will cover 9 artworks
  2. Add ULAN for top 3 artists - will cover 11 artworks
  3. Focus on high-frequency entities for maximum impact
  4. Target coverage goal: 80%+ for AAT and ULAN

Exporting detailed report...
```

**Outcome:** Comprehensive report showing current Getty vocabulary coverage (AAT: 37.11%, ULAN: 39.18%), prioritized enrichment gaps, and actionable recommendations to improve integration.

---

### Case Study 5: Artist Provenance Tracking System

**Objective:** Track the complete provenance and exhibition history of artworks by specific artists.

**Requirements:**
- Trace artwork locations (museums)
- Identify all movements associated with an artist
- Compile comprehensive artist biography
- Link to authoritative sources (DBpedia, Getty ULAN)

**Implementation:**

```javascript
// 1. Get complete artist information
async function getArtistProvenance(artistName) {
  // Fetch artworks by artist
  const artworksQuery = `
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?title ?date ?museum ?movement ?image WHERE {
  ?art rdf:type ex:Artwork ;
       ex:creator "${artistName}" .
  OPTIONAL { ?art ex:title ?title }
  OPTIONAL { ?art ex:date ?date }
  OPTIONAL { ?art ex:museum ?museum }
  OPTIONAL { ?art ex:movement ?movement }
  OPTIONAL { ?art ex:image ?image }
  
  OPTIONAL {
    ?art ex:createdBy ?artist .
    ?artist ex:name "${artistName}"
  }
}
ORDER BY ?date
  `;
  
  // Using GET method to avoid CSRF issues
  const artworksUrl = new URL('http://localhost:8000/sparql');
  artworksUrl.searchParams.append('query', artworksQuery);
  
  const [artworks, getty, stats] = await Promise.all([
    fetch(artworksUrl).then(r => r.json()),
    fetch('http://localhost:8000/getty/stats/api/').then(r => r.json()),
    fetch('http://localhost:8000/stats/api/').then(r => r.json())
  ]);
  
  // Get DBpedia info via another SPARQL query
  const dbpediaQuery = `
PREFIX ex: <http://example.org/ontology/>

SELECT ?birthDate ?birthPlace ?nationality ?movement WHERE {
  ?artist ex:name "${artistName}" ;
          ex:birthDate ?birthDate ;
          ex:birthPlace ?birthPlace ;
          ex:nationality ?nationality ;
          ex:movement ?movement .
}
LIMIT 1
  `;
  
  const dbpediaUrl = new URL('http://localhost:8000/sparql');
  dbpediaUrl.searchParams.append('query', dbpediaQuery);
  const dbpediaData = await fetch(dbpediaUrl).then(r => r.json());
  
  // Get Getty ULAN info
  const gettyInfo = getty.top_getty_artists.find(a => a.artist === artistName);
  
  // Organize data
  const museums = new Set();
  const movements = new Set();
  const dates = [];
  
  artworks.results.bindings.forEach(artwork => {
    if (artwork.museum?.value) museums.add(artwork.museum.value);
    if (artwork.movement?.value) movements.add(artwork.movement.value);
    if (artwork.date?.value) dates.push(parseInt(artwork.date.value.substring(0, 4)));
  });
  
  const biography = dbpediaData.results.bindings[0] || {};
  
  return {
    artist: artistName,
    biography: {
      birthDate: biography.birthDate?.value,
      birthPlace: biography.birthPlace?.value,
      nationality: biography.nationality?.value,
      primaryMovement: biography.movement?.value
    },
    getty: gettyInfo ? {
      ulanId: gettyInfo.ulan_id,
      ulanUrl: gettyInfo.ulan_url
    } : null,
    artworks: artworks.results.bindings.map(a => ({
      title: a.title?.value,
      date: a.date?.value,
      museum: a.museum?.value,
      movement: a.movement?.value,
      imageUrl: a.image?.value
    })),
    summary: {
      totalArtworks: artworks.results.bindings.length,
      museums: Array.from(museums),
      movements: Array.from(movements),
      activeYears: dates.length > 0 ? {
        earliest: Math.min(...dates),
        latest: Math.max(...dates),
        span: Math.max(...dates) - Math.min(...dates)
      } : null
    }
  };
}

// 2. Display provenance report
async function displayArtistProvenance(artistName) {
  console.log(`Artist Provenance Report: ${artistName}`);
  console.log('='.repeat(60) + '\n');
  
  const provenance = await getArtistProvenance(artistName);
  
  console.log('Biography:');
  console.log(`  Born: ${provenance.biography.birthDate || 'Unknown'}`);
  console.log(`  Place: ${provenance.biography.birthPlace || 'Unknown'}`);
  console.log(`  Nationality: ${provenance.biography.nationality || 'Unknown'}`);
  console.log(`  Primary Movement: ${provenance.biography.primaryMovement || 'Unknown'}\n`);
  
  if (provenance.getty) {
    console.log('Getty ULAN:');
    console.log(`  ID: ${provenance.getty.ulanId}`);
    console.log(`  URL: ${provenance.getty.ulanUrl}\n`);
  }
  
  console.log('Collection Summary:');
  console.log(`  Total Artworks in Database: ${provenance.summary.totalArtworks}`);
  console.log(`  Museums: ${provenance.summary.museums.length}`);
  console.log(`  Movements: ${provenance.summary.movements.length}`);
  
  if (provenance.summary.activeYears) {
    console.log(`  Active Period: ${provenance.summary.activeYears.earliest}-${provenance.summary.activeYears.latest}`);
    console.log(`  Career Span: ${provenance.summary.activeYears.span} years\n`);
  }
  
  console.log('Museum Holdings:');
  provenance.summary.museums.forEach(museum => {
    const count = provenance.artworks.filter(a => a.museum === museum).length;
    console.log(`  - ${museum}: ${count} artworks`);
  });
  
  console.log('\nMovement Association:');
  provenance.summary.movements.forEach(movement => {
    const count = provenance.artworks.filter(a => a.movement === movement).length;
    console.log(`  - ${movement}: ${count} artworks`);
  });
  
  console.log('\nChronological Artwork List:');
  provenance.artworks.forEach((artwork, i) => {
    console.log(`  ${i + 1}. ${artwork.title}`);
    console.log(`     Date: ${artwork.date || 'Unknown'}`);
    console.log(`     Museum: ${artwork.museum || 'Unknown'}`);
    console.log(`     Movement: ${artwork.movement || 'Unknown'}\n`);
  });
  
  return provenance;
}

// Usage - Track provenance for a real artist from the collection
const provenance = await displayArtistProvenance('Johannes Vermeer');
```

**Example Output:**
```
Artist Provenance Report: Johannes Vermeer
============================================================

Biography:
  Born: 1632-10-31
  Place: Delft
  Nationality: Netherlands
  Primary Movement: Dutch Golden Age painting

Getty ULAN:
  ID: 500032927
  URL: http://vocab.getty.edu/page/ulan/500032927

Collection Summary:
  Total Artworks in Database: 5
  Museums: 5
  Movements: 2
  Active Period: 1656-1675
  Career Span: 19 years

Museum Holdings:
  - Mauritshuis: 1 artworks
  - Metropolitan Museum of Art: 1 artworks
  - Rijksmuseum: 1 artworks
  - The Frick Collection: 1 artworks
  - Amsterdam Museum: 1 artworks

Movement Association:
  - Dutch Golden Age painting: 4 artworks
  - Baroque: 1 artworks

Chronological Artwork List:
  1. The Procuress
     Date: 1656
     Museum: Staatliche Kunstsammlungen Dresden
     Movement: Dutch Golden Age painting

  2. The Milkmaid
     Date: 1658
     Museum: Rijksmuseum
     Movement: Dutch Golden Age painting

  3. Girl with a Pearl Earring
     Date: 1665
     Museum: Mauritshuis
     Movement: Dutch Golden Age painting
```

**Outcome:** Complete provenance tracking with full biography, museum holdings, movement associations, and Getty ULAN links for authoritative artist identification.

---

## Error Handling


### Common HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful, data returned |
| 405 | Method Not Allowed | Invalid HTTP method for endpoint |
| 500 | Internal Server Error | Server error, check logs |

### Error Response Format

```json
{
  "error": "Error message describing what went wrong"
}
```

**Note:** All error responses follow this simple format with an `error` field containing the error message.

### Common Error Scenarios

#### 1. SPARQL Query Syntax Error

**Error:**
```json
{
  "error": "QueryParseException: Encountered \" \"SELEC\" \"SELEC \"\" at line 1, column 1."
}
```

**Solution:** Validate SPARQL syntax, check for typos in keywords (SELECT, WHERE, PREFIX).

#### 2. Fuseki Connection Failed

**Error:**
```json
{
  "error": "HTTPConnectionPool(host='localhost', port=3030): Max retries exceeded"
}
```

**Solution:** Ensure Fuseki server is running on port 3030. Check with:
```bash
# Windows
netstat -ano | findstr :3030

# Start Fuseki if not running
cd apache-jena-fuseki-5.6.0
fuseki-server.bat
```

#### 3. Invalid HTTP Method

**Error:**
```json
{
  "error": "Method not allowed"
}
```

**Solution:** Use GET or POST for endpoints. Check endpoint documentation for allowed methods.

### Error Handling Best Practices

```javascript
// Comprehensive error handling
async function safeAPICall(url, options = {}) {
  try {
    const response = await fetch(url, options);
    
    // Check HTTP status
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`HTTP ${response.status}: ${errorData.error || response.statusText}`);
    }
    
    const data = await response.json();
    
    // Check for application-level errors
    if (data.error) {
      console.warn('API returned error:', data.error);
      return { success: false, error: data.error, data: null };
    }
    
    return { success: true, data, error: null };
    
  } catch (error) {
    console.error('API call failed:', error);
    
    // Network error
    if (error.name === 'TypeError') {
      return {
        success: false,
        error: 'Network error - check server connectivity',
        data: null
      };
    }
    
    // Other errors
    return {
      success: false,
      error: error.message,
      data: null
    };
  }
}

// Usage
const result = await safeAPICall('http://localhost:8000/api/?page=1');

if (result.success) {
  console.log('Data:', result.data);
} else {
  console.error('Error:', result.error);
  // Handle error appropriately
}
```

### Retry Logic with Exponential Backoff

```javascript
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);
      
      if (response.ok) {
        return await response.json();
      }
      
      // Don't retry on client errors (4xx)
      if (response.status >= 400 && response.status < 500) {
        throw new Error(`Client error: ${response.status}`);
      }
      
      // Retry on server errors (5xx)
      if (attempt < maxRetries - 1) {
        const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
        console.log(`Retry attempt ${attempt + 1} after ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      
      throw new Error(`Server error: ${response.status}`);
      
    } catch (error) {
      if (attempt === maxRetries - 1) {
        throw error;
      }
    }
  }
}

// Usage
try {
  const data = await fetchWithRetry('http://localhost:8000/stats/api/');
  console.log('Statistics loaded:', data);
} catch (error) {
  console.error('Failed after retries:', error);
}
```

---

## Best Practices

### 1. Pagination Strategy

**Always use pagination for large datasets:**

```javascript
// Good: Paginated requests
async function loadAllArtworks() {
  let page = 1;
  let allArtworks = [];
  let hasMore = true;
  
  while (hasMore) {
    const response = await fetch(
      `http://localhost:8000/api/?page=${page}&per_page=50`
    );
    const data = await response.json();
    
    allArtworks.push(...data.items);
    hasMore = page < data.total_pages;
    page++;
    
    // Rate limiting - don't overwhelm server
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  return allArtworks;
}

// Bad: Requesting too much at once
// await fetch('/api/?per_page=10000') // ❌ Don't do this
```

### 2. Caching Strategy

**Implement client-side caching for static data:**

```javascript
class APICache {
  constructor(ttl = 300000) { // 5 minutes default
    this.cache = new Map();
    this.ttl = ttl;
  }
  
  get(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.ttl) {
      return cached.data;
    }
    return null;
  }
  
  set(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
  
  clear() {
    this.cache.clear();
  }
}

const apiCache = new APICache();

async function getCachedStatistics() {
  const cached = apiCache.get('statistics');
  if (cached) {
    console.log('Using cached statistics');
    return cached;
  }
  
  console.log('Fetching fresh statistics');
  const response = await fetch('http://localhost:8000/stats/api/');
  const data = await response.json();
  
  apiCache.set('statistics', data);
  return data;
}
```

### 3. SPARQL Query Optimization

**Write efficient SPARQL queries:**

```javascript
// Good: Selective query with LIMIT and FILTER
const efficientQuery = `
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?title ?creator WHERE {
  ?art rdf:type ex:Artwork ;
       ex:title ?title ;
       ex:creator ?creator .
  FILTER(?creator = "Johannes Vermeer")
}
LIMIT 100
`;

// Bad: Unfiltered query returning too much
const inefficientQuery = `
PREFIX ex: <http://example.org/ontology/>
SELECT * WHERE {
  ?s ?p ?o .
}
`; // ❌ Returns everything

// Good: Use OPTIONAL for optional fields
const goodOptionalQuery = `
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?title ?creator ?date WHERE {
  ?art rdf:type ex:Artwork ;
       ex:title ?title ;
       ex:creator ?creator .
  OPTIONAL { ?art ex:date ?date }
}
LIMIT 50
`;
```

### 4. Batch Multiple Requests

**Use Promise.all() for parallel requests:**

```javascript
// Good: Parallel requests
async function loadDashboard() {
  const [artworks, stats, getty] = await Promise.all([
    fetch('http://localhost:8000/api/?page=1').then(r => r.json()),
    fetch('http://localhost:8000/stats/api/').then(r => r.json()),
    fetch('http://localhost:8000/getty/stats/api/').then(r => r.json())
  ]);
  
  return { artworks, stats, getty };
}

// Bad: Sequential requests
async function loadDashboardSlow() {
  const artworks = await fetch('http://localhost:8000/api/?page=1').then(r => r.json());
  const stats = await fetch('http://localhost:8000/stats/api/').then(r => r.json());
  const getty = await fetch('http://localhost:8000/getty/stats/api/').then(r => r.json());
  return { artworks, stats, getty };
} // ❌ Takes 3x longer
```

### 5. URL Encoding for SPARQL

**Always encode SPARQL queries in URLs:**

```javascript
// Good: Properly encoded
const query = `
PREFIX ex: <http://example.org/ontology/>
SELECT ?title WHERE { ?art ex:title ?title } LIMIT 10
`;

const url = `http://localhost:8000/sparql?query=${encodeURIComponent(query)}`;

// Bad: Unencoded query
// const url = `http://localhost:8000/sparql?query=${query}`; // ❌ Will fail
```

### 6. Response Data Validation

**Validate response data structure:**

```javascript
function validateArtwork(artwork) {
  const required = ['title', 'creator'];
  const missing = required.filter(field => !artwork[field]);
  
  if (missing.length > 0) {
    console.warn(`Artwork missing fields: ${missing.join(', ')}`, artwork);
  }
  
  return missing.length === 0;
}

async function fetchValidatedArtworks(page) {
  const response = await fetch(`http://localhost:8000/api/?page=${page}`);
  const data = await response.json();
  
  // Filter valid artworks
  const validArtworks = data.items.filter(validateArtwork);
  
  if (validArtworks.length < data.items.length) {
    console.warn(`Filtered out ${data.items.length - validArtworks.length} invalid artworks`);
  }
  
  return { ...data, items: validArtworks };
}
```

### 7. Rate Limiting

**Implement rate limiting for bulk operations:**

```javascript
class RateLimiter {
  constructor(requestsPerSecond = 10) {
    this.delay = 1000 / requestsPerSecond;
    this.lastRequest = 0;
  }
  
  async throttle() {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequest;
    
    if (timeSinceLastRequest < this.delay) {
      await new Promise(resolve => 
        setTimeout(resolve, this.delay - timeSinceLastRequest)
      );
    }
    
    this.lastRequest = Date.now();
  }
}

const limiter = new RateLimiter(5); // 5 requests per second

async function bulkFetchArtworks(pages) {
  const results = [];
  
  for (const page of pages) {
    await limiter.throttle();
    const data = await fetch(`http://localhost:8000/api/?page=${page}`)
      .then(r => r.json());
    results.push(data);
  }
  
  return results;
}
```

### 8. Logging and Monitoring

**Log API calls for debugging:**

```javascript
class APILogger {
  constructor() {
    this.logs = [];
  }
  
  log(endpoint, method, duration, success, error = null) {
    this.logs.push({
      timestamp: new Date().toISOString(),
      endpoint,
      method,
      duration,
      success,
      error
    });
  }
  
  async fetch(url, options = {}) {
    const start = Date.now();
    const method = options.method || 'GET';
    
    try {
      const response = await fetch(url, options);
      const duration = Date.now() - start;
      
      this.log(url, method, duration, response.ok);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      return await response.json();
      
    } catch (error) {
      const duration = Date.now() - start;
      this.log(url, method, duration, false, error.message);
      throw error;
    }
  }
  
  getStats() {
    return {
      totalRequests: this.logs.length,
      successRate: this.logs.filter(l => l.success).length / this.logs.length * 100,
      avgDuration: this.logs.reduce((sum, l) => sum + l.duration, 0) / this.logs.length,
      errors: this.logs.filter(l => !l.success)
    };
  }
}

const api = new APILogger();

// Usage
await api.fetch('http://localhost:8000/api/?page=1');
await api.fetch('http://localhost:8000/stats/api/');

console.log('API Statistics:', api.getStats());
```

---

## Performance Considerations

### Query Complexity
- **Pagination:** Use `page` and `per_page` parameters
  - Default: 50 items per page
  - No hard limit enforced - use reasonable values (≤100 recommended)
  - For collection of 97 artworks: 2 pages with per_page=50
- **SPARQL:** Add LIMIT clauses to queries for performance
  - Keep queries focused with FILTER clauses
  - Use OPTIONAL for conditional fields
  - Recommended LIMIT: 100-500 for most use cases

### Response Size
- **Typical artwork response:** ~580 bytes per item (enriched with DBpedia data)
- **50 items (default page):** ~29KB compressed, ~56KB uncompressed
- **Full collection (97 items):** ~56KB compressed, ~110KB uncompressed
- **Statistics response:** ~15KB (includes top_creators, top_museums, movements)
- **Getty Stats response:** ~8KB (movements and artists with Getty IDs)

### Rate Limiting
**Note:** Currently **no rate limiting** is implemented on the server.

**Recommended client-side practices:**
- Limit to 10-20 requests per second for sustained operations
- Use batch requests (Promise.all) for parallel data fetching
- Implement exponential backoff on errors (see Error Handling section)
- Add delays between pagination loops (100-200ms)

### Caching Recommendations
**Server-side:** No caching currently implemented - all data fetched fresh from Fuseki.

**Client-side caching strategies:**
- **Statistics:** Cache for 5-10 minutes (relatively stable)
- **Artworks (paginated):** Cache individual pages for 1-2 minutes
- **Romanian Heritage (40 items):** Cache for 15-30 minutes (rarely changes)
- **Getty Stats:** Cache for 10-15 minutes (enrichment updates are infrequent)
- **Individual artwork details:** Cache for 5-10 minutes

**Note:** Since the collection is relatively small (97 artworks), aggressive caching is safe and recommended.

---

## API Versioning

**Current Version:** 1.0

The API follows semantic versioning. All endpoints are currently unversioned and represent v1.0.

Future versions will be indicated with URL prefixes (e.g., `/api/v2/artworks/`).

---

## SPARQL Prefix Reference

Common prefixes used in SPARQL queries:

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ex: <http://example.org/ontology/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
```

### Ontology Properties

| Property | Description | Example |
|----------|-------------|---------|
| `ex:title` | Artwork title | "Girl with a Pearl Earring" |
| `ex:creator` | Artist name | "Johannes Vermeer" |
| `ex:date` | Creation date | "1665" |
| `ex:museum` | Museum location | "Mauritshuis" |
| `ex:movement` | Art movement | "Dutch Golden Age painting" |
| `ex:image` | Image URL | "http://..." |
| `ex:heritage` | Romanian heritage flag | "true" |
| `ex:source` | Data source | "data.gov.ro" |
| `ex:createdBy` | Link to artist entity | URI |
| `ex:birthDate` | Artist birth date | "1632-10-31" |
| `ex:birthPlace` | Artist birthplace | "Delft" |
| `ex:nationality` | Artist nationality | "Netherlands" |

---

## Support and Resources

**Primary Documentation:** This file  
**Fuseki SPARQL Endpoint:** `http://localhost:3030/provenance/query`  
**Fuseki Web UI:** `http://localhost:3030/`  
**Django Admin:** `http://localhost:8000/admin/`

### External Resources
- **Getty ULAN:** http://vocab.getty.edu/page/ulan/
- **Getty AAT:** http://vocab.getty.edu/page/aat/
- **SPARQL 1.1 Specification:** https://www.w3.org/TR/sparql11-query/
- **Apache Jena Fuseki:** https://jena.apache.org/documentation/fuseki2/

---

## Appendix A: Complete SPARQL Examples

### Example 1: Find All Artworks by Artist

```sparql
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?title ?date ?museum WHERE {
  ?art rdf:type ex:Artwork ;
       ex:creator "Johannes Vermeer" ;
       ex:title ?title .
  OPTIONAL { ?art ex:date ?date }
  OPTIONAL { ?art ex:museum ?museum }
}
ORDER BY ?date
```

### Example 2: Count Artworks by Movement

```sparql
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?movement (COUNT(?art) as ?count) WHERE {
  ?art rdf:type ex:Artwork ;
       ex:movement ?movement .
  FILTER(?movement != "" && ?movement != "None")
}
GROUP BY ?movement
ORDER BY DESC(?count)
```

### Example 3: Find Artists Born in Specific Location

```sparql
PREFIX ex: <http://example.org/ontology/>

SELECT DISTINCT ?name ?birthDate ?birthPlace WHERE {
  ?artist ex:name ?name ;
          ex:birthPlace ?birthPlace ;
          ex:birthDate ?birthDate .
  FILTER(CONTAINS(LCASE(?birthPlace), "delft"))
}
ORDER BY ?name
```

### Example 4: Artworks with Complete Metadata

```sparql
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?title ?creator ?date ?museum ?movement WHERE {
  ?art rdf:type ex:Artwork ;
       ex:title ?title ;
       ex:creator ?creator ;
       ex:date ?date ;
       ex:museum ?museum ;
       ex:movement ?movement .
  FILTER(?creator != "Necunoscut")
  FILTER(?museum != "")
  FILTER(?movement != "")
}
LIMIT 100
```

### Example 5: Romanian Heritage Collection

```sparql
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?title ?creator ?museum WHERE {
  ?art rdf:type ex:Artwork ;
       ex:title ?title ;
       ex:creator ?creator ;
       ex:heritage "true" ;
       ex:source "data.gov.ro" .
  OPTIONAL { ?art ex:museum ?museum }
}
ORDER BY ?creator
```

### Example 6: Find Multi-Movement Artists

```sparql
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?creator (COUNT(DISTINCT ?movement) as ?movementCount) 
       (GROUP_CONCAT(DISTINCT ?movement; separator=", ") as ?movements)
WHERE {
  ?art rdf:type ex:Artwork ;
       ex:creator ?creator ;
       ex:movement ?movement .
  FILTER(?movement != "" && ?movement != "None")
}
GROUP BY ?creator
HAVING (COUNT(DISTINCT ?movement) > 1)
ORDER BY DESC(?movementCount)
LIMIT 20
```

### Example 7: Artworks by Century

```sparql
PREFIX ex: <http://example.org/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
```

---

**Last Updated:** January 13, 2026  
**API Version:** 1.0  
**Author:** Team -> Machine Love (Dulhac Alexandru and Ignat Vlad-Rovin)

