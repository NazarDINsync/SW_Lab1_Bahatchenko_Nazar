from pathlib import Path

from rdflib import Graph

HERE = Path(__file__).resolve().parent
MUSIC_TTL = HERE.parent / "01_graph" / "music.ttl"

g = Graph()
g.parse(MUSIC_TTL, format="turtle")

print(f"Прочитано трійок: {len(g)}")
