"""
Навмисно помилковий приклад і його виправлення.

Помилка: напрямок предиката ex:hasTrack переплутано. У графі трійка має вигляд
    Album  ex:hasTrack  Song
(альбом МІСТИТЬ композицію), а в помилковому запиті записано
    Song   ex:hasTrack  Album.
SPARQL не вважає це синтаксичною помилкою: шаблон просто ніде не збігається
з даними, тому запит повертає ПОРОЖНІЙ результат без жодного повідомлення.
"""

from pathlib import Path

from rdflib import Graph

HERE = Path(__file__).resolve().parent
MUSIC_TTL = HERE.parent / "01_graph" / "music.ttl"

g = Graph()
g.parse(MUSIC_TTL, format="turtle")

PREFIXES = """\
PREFIX ex:     <http://example.org/music/>
PREFIX schema: <http://schema.org/>
"""

WRONG = """
SELECT ?albumTitle
WHERE {
    ?song   schema:name  "Xtal" ;
            ex:hasTrack  ?album .          # ПОМИЛКА: напрямок навпаки
    ?album  schema:name  ?albumTitle .
}
"""

FIXED = """
SELECT ?albumTitle
WHERE {
    ?album  ex:hasTrack  ?song ;           # ВИПРАВЛЕНО: альбом -> композиція
            schema:name  ?albumTitle .
    ?song   schema:name  "Xtal" .
}
"""

DIAGNOSTIC = """
SELECT DISTINCT ?subjectType ?objectType
WHERE {
    ?s ex:hasTrack ?o ;
       a ?subjectType .
    ?o a ?objectType .
}
"""


def run(title, body):
    print("=" * 78)
    print(title)
    print("=" * 78)
    print(body.strip("\n"))
    rows = list(g.query(PREFIXES + body))
    print(f"\nРезультат ({len(rows)} рядків):")
    for row in rows:
        print("  " + " | ".join(str(cell) for cell in row))
    print()
    return rows


wrong_rows = run("1. помилковий запит: «У якому альбомі є композиція Xtal?»", WRONG)
assert not wrong_rows, "помилковий запит мав би повернути порожній результат"

print("Як знайти причину: подивитися, які типи реально стоять навколо ex:hasTrack.\n")
run("2. Діагностика: типи суб'єкта й об'єкта в трійках з ex:hasTrack", DIAGNOSTIC)
print("-> суб'єкт ex:hasTrack - MusicAlbum, об'єкт - MusicRecording, тобто напрямок Album -> Song.\n")

fixed_rows = run("3. Виправлений запит", FIXED)
assert fixed_rows, "виправлений запит мав би повернути результат"
