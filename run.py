import warnings
warnings.filterwarnings("ignore")

import os, json, time, sqlite3, datetime
import yaml
from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import OpenAI
from tracker.detect import load_brands, detect

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
orouter = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)
cfg = yaml.safe_load(open("config.yaml"))
brands = load_brands(cfg)

DB = "data/tracker.db"
os.makedirs("data", exist_ok=True)


def setup_db():
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS responses (
        run_id TEXT, query_id TEXT, query_text TEXT, provider TEXT,
        response_text TEXT, citations TEXT, latency_ms INTEGER, error TEXT
    );
    CREATE TABLE IF NOT EXISTS mentions (
        run_id TEXT, query_id TEXT, provider TEXT, brand TEXT,
        mentioned INTEGER, rank INTEGER, cited INTEGER, matched_text TEXT
    );
    """)
    con.commit()
    return con


def ask_gemini(query):
    """Returns (text, citations, latency_ms, error). Never raises."""
    start = time.time()
    try:
        r = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            ),
        )
        cites = []
        meta = r.candidates[0].grounding_metadata
        if meta and meta.grounding_chunks:
            cites = [c.web.title for c in meta.grounding_chunks if c.web]
        return r.text, cites, int((time.time() - start) * 1000), None
    except Exception as e:
        return "", [], int((time.time() - start) * 1000), str(e)


def ask_sonar(query):
    """Returns (text, citations, latency_ms, error). Never raises."""
    start = time.time()
    try:
        r = orouter.chat.completions.create(
            model="perplexity/sonar",
            max_tokens=1000,
            messages=[{"role": "user", "content": query}],
        )
        msg = r.choices[0].message
        cites = []
        for a in (getattr(msg, "annotations", None) or []):
            uc = a.get("url_citation") if isinstance(a, dict) else getattr(a, "url_citation", None)
            if uc:
                url = uc.get("url") if isinstance(uc, dict) else getattr(uc, "url", None)
                if url:
                    cites.append(url)
        return msg.content or "", cites, int((time.time() - start) * 1000), None
    except Exception as e:
        return "", [], int((time.time() - start) * 1000), str(e)


def main():
    con = setup_db()
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    providers = [("gemini", ask_gemini), ("sonar", ask_sonar)]
    print(f"Run {run_id} — {len(cfg['queries'])} queries x {len(providers)} providers\n")

    for q in cfg["queries"]:
        for pname, pfunc in providers:
            print(f"  {q['id']} [{pname}]: {q['text'][:38]}...", end=" ", flush=True)
            text, cites, ms, err = pfunc(q["text"])

            if err:
                print(f"FAILED ({err[:40]})")
            else:
                found = [m.label for m in detect(text, brands, cites) if m.mentioned]
                print(f"{ms}ms — {', '.join(found) if found else 'no brands'}")

            con.execute(
                "INSERT INTO responses VALUES (?,?,?,?,?,?,?,?)",
                (run_id, q["id"], q["text"], pname, text,
                 json.dumps(cites), ms, err),
            )
            for m in detect(text, brands, cites):
                con.execute(
                    "INSERT INTO mentions VALUES (?,?,?,?,?,?,?,?)",
                    (run_id, q["id"], pname, m.brand,
                     int(m.mentioned), m.rank, int(m.cited), m.matched_text),
                )
            con.commit()
            time.sleep(7)

    print(f"\nDone. Saved to {DB}")


if __name__ == "__main__":
    main()
