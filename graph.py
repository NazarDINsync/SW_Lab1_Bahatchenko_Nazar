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

artists = {
    "artist_aphextwin": ("Aphex Twin", "genre_ambient"),
    "artist_lfo":       ("LFO", "genre_breakbeat"),
    "artist_orbital":   ("Orbital", "genre_techno"),
    "artist_808state":  ("808 State", "genre_acidhouse"),
    "artist_plastikman": ("Plastikman", "genre_techno"), 
}
artist_uri = {}
for aid, (name, gid) in artists.items():
    uri = add_entity(aid, SCHEMA.MusicGroup, name)
    g.add((uri, EX.hasGenre, genre_uri[gid]))
    artist_uri[aid] = uri

albums = [
    ("album_selectedambient", "Selected Ambient Works 85-92", "artist_aphextwin", 1992, "label_warp"),
    ("album_frequencies",     "Frequencies",                   "artist_lfo",       1991, "label_warp"),
    ("album_orbital1",        "Orbital (Green Album)",         "artist_orbital",   1991, "label_rs"),
    ("album_exel8",           "ex.el8",                        "artist_808state",  1991, None),  # без лейбла навмисно
]

album_uri = {}
for alid, title, aid, year, lid in albums:
    uri = add_entity(alid, SCHEMA.MusicAlbum, title)
    g.add((uri, EX.releasedBy, artist_uri[aid]))
    g.add((uri, SCHEMA.datePublished, Literal(year, datatype=XSD.gYear)))
    if lid is not None:
        g.add((uri, EX.recordLabel, label_uri[lid]))
    album_uri[alid] = uri

print(len(g))