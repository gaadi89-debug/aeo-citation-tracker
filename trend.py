import sqlite3, yaml
from rich.console import Console
from rich.table import Table

cfg = yaml.safe_load(open("config.yaml"))
con = sqlite3.connect("data/tracker.db")
console = Console()

brands = [(b["key"], b["label"]) for b in cfg["brands"]]
providers = [p[0] for p in con.execute(
    "SELECT DISTINCT provider FROM responses ORDER BY provider").fetchall()]

for prov in providers:
    runs = [r[0] for r in con.execute(
        "SELECT DISTINCT run_id FROM responses WHERE provider=? ORDER BY run_id",
        (prov,)).fetchall()]

    t = Table(title=f"{prov} — share of voice over time")
    t.add_column("Brand", style="cyan")
    for r in runs:
        t.add_column(r[4:8], justify="center")   # MMDD

    for bkey, label in brands:
        row = [label]
        for r in runs:
            ok = [x[0] for x in con.execute(
                "SELECT query_id FROM responses WHERE run_id=? AND provider=? "
                "AND error IS NULL", (r, prov)).fetchall()]
            if not ok:
                row.append("[yellow]—[/]")
                continue
            n = con.execute(
                "SELECT COUNT(*) FROM mentions WHERE run_id=? AND provider=? "
                "AND brand=? AND mentioned=1 AND query_id IN (%s)" %
                ",".join("?" * len(ok)),
                (r, prov, bkey, *ok)).fetchone()[0]
            pct = 100 * n // len(ok)
            colour = "green" if bkey == "simplismart" and n else "white"
            row.append(f"[{colour}]{n}/{len(ok)}[/]")
        t.add_row(*row)

    console.print(t)
    console.print("[dim]— means no queries succeeded in that run[/]\n")
