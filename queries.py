"""
SPARQL-запити до графа music.ttl (предметна область: Музика).

1. Композиції альбому (зв'язок Album -> Song, ORDER BY)
2. Альбоми 1991-1992 (FILTER)
3. Виконавець(ці) з найбільшою кількістю альбомів (COUNT, підзапит з MAX)
4. Середня тривалість пісень по жанру (AVG, 3 хопи: Song <- Album -> Artist -> Genre)
5. Виконавці без альбомів, лише сингли (FILTER NOT EXISTS)
"""

from rdflib import Graph

g = Graph()
g.parse("music.ttl", format="turtle")

PREFIXES = """\
PREFIX ex:     <http://example.org/music/>
PREFIX schema: <http://schema.org/>
PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
"""

queries = [
    (
        "Q1. Композиції альбому «Selected Ambient Works 85-92», від найдовшої до найкоротшої (ORDER BY)",
        """
SELECT ?title ?duration
WHERE {
    ?album  a               schema:MusicAlbum ;
            schema:name     "Selected Ambient Works 85-92" ;
            ex:hasTrack     ?song .
    ?song   schema:name     ?title ;
            ex:duration     ?duration .
}
ORDER BY DESC(?duration)
""",
    ),
    (
        "Q2. Альбоми, випущені у 1991-1992 роках (FILTER)",
        """
SELECT ?title ?year
WHERE {
    ?album  a                    schema:MusicAlbum ;
            schema:name          ?title ;
            schema:datePublished ?year .
    FILTER (xsd:integer(STR(?year)) >= 1991 && xsd:integer(STR(?year)) <= 1992)
}
ORDER BY ?year ?title
""",
    ),
    (
        "Q3. Виконавець з найбільшою кількістю альбомів (COUNT; за рівності - усі лідери)",
        """
SELECT ?artistName ?albums
WHERE {
    {
        SELECT ?artist (COUNT(?album) AS ?albums)
        WHERE { ?album a schema:MusicAlbum ; ex:releasedBy ?artist . }
        GROUP BY ?artist
    }
    {
        SELECT (MAX(?n) AS ?maxAlbums)
        WHERE {
            SELECT ?a (COUNT(?al) AS ?n)
            WHERE { ?al a schema:MusicAlbum ; ex:releasedBy ?a . }
            GROUP BY ?a
        }
    }
    FILTER (?albums = ?maxAlbums)
    ?artist schema:name ?artistName .
}
ORDER BY ?artistName
""",
    ),
    (
        "Q4. Середня тривалість пісень за жанром (AVG; шлях Song <- Album -> Artist -> Genre)",
        """
SELECT ?genreName (AVG(?duration) AS ?avgDuration) (COUNT(?song) AS ?songs)
WHERE {
    ?song   ex:duration     ?duration .
    ?album  ex:hasTrack     ?song ;
            ex:releasedBy   ?artist .
    ?artist ex:hasGenre     ?genre .
    ?genre  schema:name     ?genreName .
}
GROUP BY ?genreName
ORDER BY DESC(?avgDuration)
""",
    ),
    (
        "Q5. Виконавці, які мають лише сингли, без жодного альбому (FILTER NOT EXISTS)",
        """
SELECT DISTINCT ?artistName ?title
WHERE {
    ?song   ex:performedBy  ?artist ;
            schema:name     ?title .
    ?artist schema:name     ?artistName .
    FILTER NOT EXISTS { ?album ex:releasedBy ?artist . }
}
ORDER BY ?artistName ?title
""",
    ),
]


def print_table(result):
    """Друкує результат SELECT-запиту як вирівняну таблицю."""
    headers = [str(v) for v in result.vars]
    rows = [[str(cell) if cell is not None else "" for cell in row] for row in result]
    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h)
              for i, h in enumerate(headers)]
    line = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("-+-".join("-" * w for w in widths))
    for r in rows:
        print(" | ".join(c.ljust(w) for c, w in zip(r, widths)))
    print(f"({len(rows)} рядків)")


for title, body in queries:
    print("=" * 78)
    print(title)
    print("=" * 78)
    print("Запит:")
    print(body.strip("\n"))
    print("\nРезультат:")
    print_table(g.query(PREFIXES + body))
    print()
