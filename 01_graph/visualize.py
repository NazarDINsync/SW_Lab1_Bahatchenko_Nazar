"""
Візуалізація RDF-графа music.ttl (networkx + matplotlib) -> graph.png

Вузли - сутності (колір І форма залежать від класу, підпис на кожному вузлі),
ребра - зв'язки між сутностями (стиль лінії залежить від предиката).
Літерали (назви, тривалість, рік) на малюнок не виносяться, щоб він лишався читабельним.
"""

import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D
from rdflib import Graph, Namespace, RDF, URIRef

HERE = Path(__file__).resolve().parent

EX = Namespace("http://example.org/music/")
SCHEMA = Namespace("http://schema.org/")

g = Graph()
g.parse(HERE / "music.ttl", format="turtle")

# клас -> (підпис у легенді, колір, форма вузла, розмір)
CLASSES = {
    SCHEMA.MusicGroup:     ("Виконавець (schema:MusicGroup)",   "#2a78d6", "o", 900),
    SCHEMA.MusicAlbum:     ("Альбом (schema:MusicAlbum)",       "#eb6834", "s", 900),
    SCHEMA.MusicRecording: ("Композиція (schema:MusicRecording)", "#1baf7a", "D", 450),
    EX.Genre:              ("Жанр (ex:Genre)",                  "#eda100", "^", 900),
    EX.RecordLabel:        ("Лейбл (ex:RecordLabel)",           "#e87ba4", "p", 900),
}

# предикат -> (підпис, колір, стиль лінії)
PREDICATES = {
    EX.hasTrack:     ("ex:hasTrack (альбом → композиція)",   "#52514e", "solid"),
    EX.performedBy:  ("ex:performedBy (композиція → виконавець)", "#52514e", "dotted"),
    EX.releasedBy:   ("ex:releasedBy (альбом → виконавець)", "#0b0b0b", "solid"),
    EX.hasGenre:     ("ex:hasGenre (виконавець → жанр)",     "#0b0b0b", "dashed"),
    EX.recordLabel:  ("ex:recordLabel (альбом → лейбл)",     "#0b0b0b", "dashdot"),
}

SURFACE = "#fcfcfb"
INK = "#0b0b0b"

G = nx.MultiDiGraph()
kind = {}
for node, _, cls in g.triples((None, RDF.type, None)):
    if cls in CLASSES:
        kind[node] = cls
        title = str(g.value(node, SCHEMA.name))
        year = g.value(node, SCHEMA.datePublished)
        if year is not None:
            title += f" ({year})"
        G.add_node(node, label="\n".join(textwrap.wrap(title, 16)))

for s, p, o in g:
    if p in PREDICATES and s in kind and o in kind:
        G.add_edge(s, o, predicate=p)

print(f"Вузлів: {G.number_of_nodes()}, ребер: {G.number_of_edges()}")



def layered_layout():
    """Колонки зліва направо: лейбл | альбом | композиція | виконавець | жанр.
    Рядки групуються по виконавцях, тому лінії майже не перетинаються."""
    def by_name(nodes):
        return sorted(nodes, key=lambda n: str(g.value(n, SCHEMA.name)))

    artists = [EX.artist_aphextwin, EX.artist_lfo, EX.artist_808state,
               EX.artist_orbital, EX.artist_plastikman]
    gap_song, gap_group, gap_artist = 0.65, 0.45, 0.6
    x = {"label": -1.0, "album": 0.0, "song": 1.0, "artist": 2.0, "genre": 3.0}
    pos, cursor = {}, 0.0

    def mean(nodes):
        return sum(pos[n][1] for n in nodes) / len(nodes)

    for artist in artists:
        albums = sorted(g.subjects(EX.releasedBy, artist),
                        key=lambda a: str(g.value(a, SCHEMA.datePublished)))
        groups = [(a, by_name(g.objects(a, EX.hasTrack))) for a in albums]
        in_album = {s for _, songs in groups for s in songs}
        singles = by_name(s for s in g.subjects(EX.performedBy, artist) if s not in in_album)
        if singles:
            groups.append((None, singles))
        for album, songs in groups:
            for song in songs:
                pos[song] = (x["song"], cursor)
                cursor -= gap_song
            cursor -= gap_group
            if album is not None:
                pos[album] = (x["album"], mean(songs))
        pos[artist] = (x["artist"], mean([n for n in pos if n in set(g.subjects(EX.performedBy, artist))]))
        cursor -= gap_artist

    for genre in set(g.subjects(RDF.type, EX.Genre)):
        pos[genre] = (x["genre"], mean(list(g.subjects(EX.hasGenre, genre))))
    labels = list(g.subjects(RDF.type, EX.RecordLabel))
    used = [l for l in labels if any(True for _ in g.subjects(EX.recordLabel, l))]
    for label in used:
        pos[label] = (x["label"], mean(list(g.subjects(EX.recordLabel, label))))
    for i, label in enumerate(l for l in labels if l not in used):
        pos[label] = (x["label"], cursor - i * gap_artist)   # без альбомів - унизу
    return pos


pos = layered_layout()

fig, ax = plt.subplots(figsize=(18, 15), dpi=150)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

for p, (_, color, style) in PREDICATES.items():
    edges = [(u, v) for u, v, d in G.edges(data=True) if d["predicate"] == p]
    nx.draw_networkx_edges(
        G, pos, edgelist=edges, ax=ax, edge_color=color, style=style, width=1.4,
        alpha=0.75, arrows=True, arrowstyle="-|>", arrowsize=16,
        node_size=700, connectionstyle="arc3,rad=0.0",
    )

for cls, (_, color, shape, size) in CLASSES.items():
    nodes = [n for n, c in kind.items() if c == cls]
    collection = nx.draw_networkx_nodes(
        G, pos, nodelist=nodes, ax=ax, node_color=color, node_shape=shape,
        node_size=size, edgecolors=SURFACE, linewidths=2,
    )
    collection.set_zorder(4)

for node, (px, py) in pos.items():
    marker_size = CLASSES[kind[node]][3]            # площа маркера у pt^2
    gap_pt = marker_size ** 0.5 / 2 + 4             # відступ від центру до підпису, pt
    ax.annotate(G.nodes[node]["label"], (px, py), xytext=(0, -gap_pt),
                textcoords="offset points", ha="center", va="top",
                fontsize=9, color=INK, zorder=5,
                path_effects=[pe.withStroke(linewidth=3, foreground=SURFACE)])

node_handles = [
    Line2D([], [], marker=shape, linestyle="", markersize=13, markerfacecolor=color,
           markeredgecolor=SURFACE, label=label)
    for label, color, shape, _ in CLASSES.values()
]
edge_handles = [
    Line2D([], [], color=color, linestyle=style, linewidth=2, label=label)
    for label, color, style in PREDICATES.values()
]
legend = ax.legend(handles=node_handles + edge_handles, loc="upper center",
                   bbox_to_anchor=(0.5, -0.01), ncol=2, frameon=True,
                   facecolor=SURFACE, edgecolor="#d9d8d3", fontsize=11,
                   title="Класи та зв'язки", title_fontsize=12)
legend.get_title().set_color(INK)
for t in legend.get_texts():
    t.set_color(INK)

ax.set_title("RDF-граф предметної області «Музика» (music.ttl)", fontsize=16,
             color=INK, pad=14)
ax.set_xlim(-1.5, 3.5)
ax.margins(y=0.04)
ax.axis("off")
fig.tight_layout()
fig.savefig(HERE / "graph.png", facecolor=SURFACE)
print("Зображення збережено у graph.png")
