from rdflib import Graph

g = Graph()
g.parse("music.ttl", format="turtle")

print(f"Прочитано трійок: {len(g)}")