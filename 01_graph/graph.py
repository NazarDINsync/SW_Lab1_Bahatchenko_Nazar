"""
Предметна область: Музика

5 питань:
1. Композиції певного альбому (join + ORDER BY)
2. Альбоми 1991-1992 (FILTER)
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

from pathlib import Path

from rdflib import Graph, Namespace, Literal, RDF, RDFS, URIRef
from rdflib.namespace import XSD

HERE = Path(__file__).resolve().parent

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
    ("album_rdjalbum",        "Richard D. James Album",        "artist_aphextwin", 1996, "label_warp"),  # 2-й альбом Aphex Twin (для Q3)
]

album_uri = {}
for alid, title, aid, year, lid in albums:
    uri = add_entity(alid, SCHEMA.MusicAlbum, title)
    g.add((uri, EX.releasedBy, artist_uri[aid]))
    g.add((uri, SCHEMA.datePublished, Literal(year, datatype=XSD.gYear)))
    if lid is not None:
        g.add((uri, EX.recordLabel, label_uri[lid]))
    album_uri[alid] = uri

songs = [
    ("song_xtalcal",       "Xtal",              "artist_aphextwin", "album_selectedambient", 268),
    ("song_tha",           "Tha",               "artist_aphextwin", "album_selectedambient", 574),
    ("song_lfo_track",     "LFO",               "artist_lfo",       "album_frequencies",      316),
    ("song_mentaldread",   "Mental Dread",       "artist_lfo",       "album_frequencies",      248),
    ("song_chime",         "Chime",             "artist_orbital",   "album_orbital1",         410),
    ("song_midnight",      "Midnight",          "artist_orbital",   "album_orbital1",         362),
    ("song_pacman",        "Pacman",            "artist_808state",  "album_exel8",            265),
    ("song_cubik",         "Cubik",             "artist_808state",  "album_exel8",            300),
    ("song_fourtrack",     "4",                 "artist_aphextwin", "album_rdjalbum",         217),
    ("song_girlboy",       "Girl/Boy Song",     "artist_aphextwin", "album_rdjalbum",         244),
    ("song_spastik",       "Spastik",          "artist_plastikman", None, 391),   # сингл, без альбому
    ("song_koma",          "Koma",              "artist_plastikman", None, 420),   # сингл, без альбому
]

for sid, title, aid, alid, duration in songs:
    uri = add_entity(sid, SCHEMA.MusicRecording, title)
    g.add((uri, EX.performedBy, artist_uri[aid]))
    g.add((uri, EX.duration, Literal(duration, datatype=XSD.integer)))
    if alid is not None:
        g.add((album_uri[alid], EX.hasTrack, uri))

print(f"Кількість трійок: {len(g)}")

entity_types = set(g.objects(None, RDF.type))
print(f"Кількість типів сутностей: {len(entity_types)}")
for t in entity_types:
    print(f"  - {t}")

all_resources = set(g.subjects()) | {o for o in g.objects() if isinstance(o, URIRef)}
print(f"Кількість екземплярів (URI-ресурсів): {len(all_resources)}")

g.serialize(destination=str(HERE / "music.ttl"), format="turtle")
print("Граф збережено у music.ttl")

xml_path = HERE / "music.rdf"
g.serialize(destination=xml_path, format="xml")
print(f"Граф збережено у другому форматі: {xml_path}")

def print_header(title):
    print(f"\n{'=' * 70}")
    print(f" {title}")
    print(f"{'=' * 70}")

def short(uri):
    s = str(uri)
    if s.startswith(str(EX)):
        return "ex:" + s[len(str(EX)):]
    if s.startswith(str(SCHEMA)):
        return "schema:" + s[len(str(SCHEMA)):]
    if s.startswith(str(RDFS)):
        return "rdfs:" + s[len(str(RDFS)):]
    if s.startswith(str(RDF)):
        return "rdf:" + s[len(str(RDF)):]
    return s

print_header("Перші 10 трійок графа")
for i, (s, p, o) in enumerate(g):
    if i >= 10:
        break
    print(f"  {short(s):<28} {short(p):<20} {short(o)}")
    
target = EX.artist_aphextwin

print_header(f"Трійки, пов'язані з {short(target)}")

print("\n-- Як суб'єкт (властивості цієї сутності) --")
for p, o in g.predicate_objects(subject=target):
    print(f"  {short(target):<20} --{short(p):<18}--> {short(o)}")

print("\n-- Як об'єкт (хто на неї посилається) --")
for s, p in g.subject_predicates(object=target):
    print(f"  {short(s):<20} --{short(p):<18}--> {short(target)}")

print()