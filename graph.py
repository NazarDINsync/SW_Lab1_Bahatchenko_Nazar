"""
Предметна область: Музика

5 питань:
1. Композиції певного альбому (join + ORDER BY)
2. Альбоми 2015-2022 (FILTER)
3. Виконавець з найбільшою к-тю альбомів (COUNT)
4. Середня тривалість пісень по жанру (AVG, 3 хопи: Song->Album->Artist->Genre)
5. Виконавці без альбомів, лише сингли (FILTER NOT EXISTS)

Класи: Song, Album, Artist, Genre, RecordLabel

Предикати:
- ex:hasTrack       Album -> Song
- ex:performedBy    Song -> Artist
- ex:releasedBy     Album -> Artist
- ex:hasGenre       Artist -> Genre
- schema:datePublished  Album -> рік
- ex:duration       Song -> секунди
- ex:recordLabel    Album -> RecordLabel (не в усіх альбомів)
"""

from rdflib import Graph, Namespace, Literal, RDF, RDFS, URIRef
from rdflib.namespace import XSD

EX = Namespace("http://example.org/music/")   
SCHEMA = Namespace("http://schema.org/")

g = Graph()
g.bind("ex", EX)
g.bind("schema", SCHEMA)

def add_entity(local_id, rdf_type, label):
    uri = EX[local_id]
    g.add((uri, RDF.type, rdf_type))
    g.add((uri, RDFS.label, Literal(label, lang="uk")))
    g.add((uri, SCHEMA.name, Literal(label)))
    return uri

genres = {
    "genre_acidhouse": "Acid House",
    "genre_techno":    "Techno",
    "genre_ambient":   "Ambient",
    "genre_breakbeat": "Breakbeat",
}
genre_uri = {}

for gid, name in genres.items():
    genre_uri[gid] = add_entity(gid, EX.Genre, name)

labels = {
    "label_warp":   "Warp Records",
    "label_rs":     "R&S Records",
    "label_mute":   "Mute Records",
}
label_uri = {}

for lid, name in labels.items():
    label_uri[lid] = add_entity(lid, EX.RecordLabel, name)