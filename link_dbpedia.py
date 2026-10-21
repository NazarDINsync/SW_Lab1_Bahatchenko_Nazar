"""
Зв'язок власного графа з DBpedia через owl:sameAs.

Чому owl:sameAs: ex:artist_aphextwin і dbr:Aphex_Twin описують ОДНУ Й ТУ САМУ
реальну сутність (музиканта), тобто потрібна ідентичність, а не просто
"пов'язаність" (rdfs:seeAlso) чи "схожість" (skos:closeMatch). Після такого
твердження всі факти про dbr:Aphex_Twin вважаються фактами і про ex:artist_aphextwin.

Кроки:
1. Додати owl:sameAs до графа -> music_linked.ttl (music.ttl не змінюється).
2. Завантажити з DBpedia вибрані властивості пов'язаних ресурсів (CONSTRUCT);
   відповідь кешується у dbpedia_cache.ttl, щоб демо працювало й без мережі.
3. Виконати ОДИН SPARQL-запит, що поєднує дані обох графів.
"""

import urllib.parse
import urllib.request

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL

ENDPOINT = "https://dbpedia.org/sparql"
CACHE_FILE = "dbpedia_cache.ttl"

EX = Namespace("http://example.org/music/")
DBR = Namespace("http://dbpedia.org/resource/")

LINKS = {
    EX.artist_aphextwin: DBR["Aphex_Twin"],
    EX.artist_808state:  DBR["808_State"],
}

g = Graph()
g.parse("music.ttl", format="turtle")
g.bind("owl", OWL)
g.bind("dbr", DBR)

for local, remote in LINKS.items():
    g.add((local, OWL.sameAs, remote))
    print(f"{local}  owl:sameAs  {remote}")

g.serialize(destination="music_linked.ttl", format="turtle")
print("\nГраф із зв'язками збережено у music_linked.ttl")


def fetch_dbpedia(resources):
    """CONSTRUCT-запит до DBpedia: лише потрібні властивості вказаних ресурсів."""
    values = " ".join(f"<{r}>" for r in resources)
    query = f"""
    PREFIX dbo:  <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    CONSTRUCT {{ ?s ?p ?o }}
    WHERE {{
        VALUES ?s {{ {values} }}
        VALUES ?p {{ dbo:genre dbo:activeYearsStartYear dbo:birthDate dbo:recordLabel rdfs:label }}
        ?s ?p ?o .
        FILTER (!isLiteral(?o) || lang(?o) = "" || lang(?o) = "en")
    }}
    """
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(url, headers={
        "Accept": "text/turtle",
        "User-Agent": "SW-Lab1-student/1.0",
    })
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.read().decode("utf-8")


remote = Graph()
try:
    remote.parse(data=fetch_dbpedia(LINKS.values()), format="turtle")
    remote.serialize(destination=CACHE_FILE, format="turtle")
    print(f"Отримано {len(remote)} трійок з DBpedia (кеш: {CACHE_FILE})")
except Exception as e:
    print(f"DBpedia недоступна ({e}); беремо кеш {CACHE_FILE}")
    remote.parse(CACHE_FILE, format="turtle")

merged = g + remote

QUERY = """
PREFIX ex:     <http://example.org/music/>
PREFIX schema: <http://schema.org/>
PREFIX owl:    <http://www.w3.org/2002/07/owl#>
PREFIX dbo:    <http://dbpedia.org/ontology/>
PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>

SELECT ?name ?album ?albumYear ?activeSince
       (xsd:integer(STR(?albumYear)) - xsd:integer(STR(?activeSince)) AS ?yearsIntoCareer)
       (GROUP_CONCAT(DISTINCT STRAFTER(STR(?dbpGenre), "resource/"); separator=", ") AS ?dbpediaGenres)
WHERE {
    ?artist owl:sameAs ?dbp ;
            schema:name ?name .
    ?albumRes ex:releasedBy ?artist ;
              schema:name ?album ;
              schema:datePublished ?albumYear .
    ?dbp dbo:activeYearsStartYear ?activeSince ;
         dbo:genre ?dbpGenre .
}
GROUP BY ?name ?album ?albumYear ?activeSince
ORDER BY ?name ?albumYear
"""

print("\nЗапит, що поєднує власний граф і DBpedia:")
print(QUERY.strip("\n"))
print("\nРезультат:")
res = merged.query(QUERY)
for row in res:
    print(f"{row.name} - «{row.album}» ({row.albumYear})")
    print(f"    у DBpedia активний з {row.activeSince}, альбом вийшов через {row.yearsIntoCareer} р.")
    print(f"    жанри в DBpedia: {row.dbpediaGenres}")
