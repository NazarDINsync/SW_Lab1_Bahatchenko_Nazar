"""
Демо: проганяє всі кроки лабораторної по черзі.

Усе виконується в КОПІЇ (demo_run/), тож готові файли в папках 01_...05_
(music.ttl, graph.png, music_linked.ttl тощо) не перезаписуються.

Використання:
    python demo.py              # усі кроки
    python demo.py 3            # лише крок 03 (граф береться з кроку 01 у копії)
    python demo.py 1 3          # кілька кроків
"""

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "demo_run"

STEPS = [
    ("01_graph",         "graph.py",         "Побудова графа, запис у Turtle і RDF/XML, трійки Aphex Twin"),
    ("01_graph",         "visualize.py",     "Візуалізація графа -> graph.png"),
    ("02_read_turtle",   "read_graph.py",    "Читання music.ttl назад"),
    ("03_sparql",        "queries.py",       "П'ять SPARQL-запитів"),
    ("04_dbpedia",       "link_dbpedia.py",  "owl:sameAs і запит по двох графах (DBpedia)"),
    ("05_error_example", "error_example.py", "Помилковий запит, діагностика, виправлення"),
]

wanted = {int(a) for a in sys.argv[1:]}

if RUN.exists():
    shutil.rmtree(RUN)
RUN.mkdir()
for folder in sorted({f for f, _, _ in STEPS}):
    shutil.copytree(HERE / folder, RUN / folder, ignore=shutil.ignore_patterns("__pycache__"))

if wanted:
    # якщо запущено не крок 01, граф усе одно потрібен: будуємо його в копії тихо
    if 1 not in wanted:
        subprocess.run([sys.executable, str(RUN / "01_graph" / "graph.py")],
                       check=True, stdout=subprocess.DEVNULL)

for folder, script, title in STEPS:
    if wanted and int(folder[:2]) not in wanted:
        continue
    print("\n" + "#" * 78, flush=True)
    print(f"# {folder}/{script}: {title}", flush=True)
    print("#" * 78, flush=True)
    subprocess.run([sys.executable, str(RUN / folder / script)], check=True)

print(f"\nГотово. Копія результатів: {RUN}")
