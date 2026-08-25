import sqlite3, yaml
from rich.console import Console
from rich.table import Table

cfg = yaml.safe_load(open("config.yaml"))
con = sqlite3.connect("data/tracker.db")
console = Console()

runs = [r[0] for r in con.execute(
    "SELECT DISTINCT run_id FROM mentions ORDER BY run_id").fetchall()]
latest = runs[-1]

brands = [(b["key"], b["label"]) for b in cfg["brands"]]
queries = [(q["id"], q["text"]) for q in cfg["queries"]]

t = Table(title=f"AEO Citation Matrix — run {latest}")
t.add_column("Query", style="cyan", no_wrap=False, max_width=42)
for _, label in brands:
    t.add_column(label, justify="center")

for qid, qtext in queries:
    row = [f"{qid}  {qtext[:38]}"]
    for bkey, _ in brands:
        hit = con.execute(
            "SELECT mentioned FROM mentions WHERE run_id=? AND query_id=? AND brand=?",
            (latest, qid, bkey)).fetchone()
        row.append("[green]YES[/]" if hit and hit[0] else "[dim]·[/]")
    t.add_row(*row)

console.print(t)

s = Table(title="Share of voice")
s.add_column("Brand")
s.add_column("Queries", justify="right")
s.add_column("Share", justify="right")

total = len(queries)
scores = []
for bkey, label in brands:
    n = con.execute(
        "SELECT COUNT(*) FROM mentions WHERE run_id=? AND brand=? AND mentioned=1",
        (latest, bkey)).fetchone()[0]
    scores.append((n, label))

for n, label in sorted(scores, reverse=True):
    bar = "█" * n + "░" * (total - n)
    s.add_row(label, f"{n}/{total}", f"{bar}  {100*n//total}%")

console.print(s)

if len(runs) > 1:
    console.print(f"\n[dim]{len(runs)} runs logged — trend available[/]")
else:
    console.print("\n[dim]1 run logged. Run again tomorrow for trend data.[/]")
