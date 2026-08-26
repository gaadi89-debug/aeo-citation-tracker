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
providers = [p[0] for p in con.execute(
    "SELECT DISTINCT provider FROM responses WHERE run_id=? ORDER BY provider",
    (latest,)).fetchall()]

for prov in providers:
    ok = {r[0] for r in con.execute(
        "SELECT query_id FROM responses WHERE run_id=? AND provider=? AND error IS NULL",
        (latest, prov)).fetchall()}

    t = Table(title=f"{prov} — run {latest}  ({len(ok)}/{len(queries)} queries succeeded)")
    t.add_column("Query", style="cyan", max_width=40)
    for _, label in brands:
        t.add_column(label, justify="center")

    for qid, qtext in queries:
        row = [f"{qid}  {qtext[:34]}"]
        for bkey, _ in brands:
            if qid not in ok:
                row.append("[yellow]?[/]")
                continue
            hit = con.execute(
                "SELECT mentioned FROM mentions WHERE run_id=? AND query_id=? "
                "AND provider=? AND brand=?", (latest, qid, prov, bkey)).fetchone()
            row.append("[green]YES[/]" if hit and hit[0] else "[dim]·[/]")
        t.add_row(*row)

    console.print(t)

    s = Table(title=f"{prov} — share of voice")
    s.add_column("Brand")
    s.add_column("Seen", justify="right")
    s.add_column("Share", justify="right")

    total = len(ok)
    scores = []
    for bkey, label in brands:
        n = con.execute(
            "SELECT COUNT(*) FROM mentions WHERE run_id=? AND provider=? "
            "AND brand=? AND mentioned=1 AND query_id IN (%s)" %
            ",".join("?" * len(ok)),
            (latest, prov, bkey, *ok)).fetchone()[0] if ok else 0
        scores.append((n, label))

    for n, label in sorted(scores, reverse=True):
        bar = "█" * n + "░" * (total - n) if total else ""
        pct = f"{100*n//total}%" if total else "n/a"
        s.add_row(label, f"{n}/{total}", f"{bar}  {pct}")

    console.print(s)
    console.print()

console.print(f"[dim]{len(runs)} runs logged[/]")
