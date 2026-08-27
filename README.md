# AEO Citation Tracker

Tracks whether Simplismart and four competitors (Baseten, Fireworks AI, Together AI, Modal)
get cited by AI answer engines for eight category-relevant search queries.

Runs on a schedule you control, logs every response to SQLite, and prints a report that
answers three questions at a glance: **are we showing up, are competitors showing up more,
and is it changing over time?**

## Why grounded search

A plain API call to an LLM does not search the web — it answers from training data. That
measures what a model *memorised*, not what it *cites today*, which is a different metric
and not what AEO is about.

Both providers here are search-grounded:

| Provider | Model | Grounding |
|---|---|---|
| Google Gemini | `gemini-2.5-flash` | `google_search` tool enabled |
| Perplexity (via OpenRouter) | `perplexity/sonar` | native web search |

Two providers, chosen for a genuine free tier and for native grounding with real citation
URLs. Both are named in the brief.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install google-genai openai pyyaml rich python-dotenv
```

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
```

Gemini keys come from [aistudio.google.com](https://aistudio.google.com) (free tier, no card).
OpenRouter keys from [openrouter.ai](https://openrouter.ai) — Sonar needs a small credit balance.

`.env` is gitignored and never committed.

## Usage

```bash
python3 run.py        # query all 8 queries x 2 providers, log to SQLite
python3 report.py     # print the citation matrix and share of voice
```

A run takes about four minutes. There is a 7-second sleep between calls because the Gemini
free tier allows roughly 10 requests/minute.

## How it works

```
config.yaml          8 queries + 5 brands with regex variants
    |
    v
run.py               calls each provider, catches every error
    |
    v
tracker/detect.py    brand matching, first-mention rank, citation-domain check
    |
    v
data/tracker.db      one row per query x provider, per run
    |
    v
report.py            per-provider matrix + share of voice
```

### Brand detection

Substring matching breaks immediately on this brand set:

- **Together AI** — "together" is an ordinary English word. "*teams working together on
  inference*" is a false positive. The pattern requires `together.ai` or `Together AI`.
- **Modal** — collides with `modality`, `multimodal`, `modal window`, `modal verb`. Bare
  "Modal" is only accepted capitalised and with a negative lookahead for those giveaway words.
- **Fireworks AI** — real output contained "Firework AI", singular. The pattern allows both.
- **Simplismart** — appears as `Simplismart`, `SimpliSmart`, `Simpli Smart`.

`tests/test_detect.py` covers these cases. Run with `pytest -q`.

Detection records more than a boolean: **rank** (order of first mention within an answer,
since being named first differs from being named eighth) and **cited** (whether the brand's
own domain appears in the returned source URLs, which can be true even when the name never
appears in prose).

### Failure handling

Every API call returns a tuple rather than raising, so one failure never kills a run. Errors
are written to the `error` column.

`report.py` distinguishes three states, which matters more than it sounds:

- `YES` — brand mentioned
- `·` — brand not mentioned
- `?` — query failed, so the answer is unknown

A failed query is **not** counted as "not mentioned." Share of voice is computed only over
queries that actually succeeded, and each table shows `n/8 queries succeeded` in its title.
Without this, a rate-limited run would report every brand at 0% and look like real data.

## Limitations

- **n=1 per query.** LLM output is nondeterministic. Two Gemini runs seven minutes apart
  disagreed on q4. A production version would run k=3–5 and report mention *rate*.
- **Gemini free tier caps at ~250 requests/day**, which is reached quickly during development.
- **Gemini returns citations as `vertexaisearch` redirect URLs**, not real domains, so
  domain matching only works against Sonar's citations.
- No scheduling, alerting, geographic variation, or prompt paraphrasing.

## Repo layout

```
config.yaml            queries and brand patterns
run.py                 the runner
report.py              CLI report
tracker/detect.py      brand detection
tests/test_detect.py   detection tests
data/tracker.db        logged runs (committed as evidence)
NOTES.md               blockers and findings
```
