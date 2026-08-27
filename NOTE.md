# AEO Citation Tracker — note

## What I built

A CLI tool that runs the 8 queries against two **search-grounded** answer engines —
Gemini 2.5 Flash with `google_search`, and Perplexity Sonar via OpenRouter — logs every
response to SQLite, and prints three views: a citation matrix, share of voice, and a
trend across runs.

Grounding was the key call. A plain API call answers from training memory, not from a
live search, which measures the wrong thing. Both engines here search the web.

## What it found

**Simplismart appears in 1 of 8 queries, on both engines independently. That one is q7 —
our own brand name.** Across 6 runs it has never gone above 1.

- **"Baseten alternatives"** returns Baseten, Fireworks AI, Together AI, Modal. Not us.
- **"AI inference platforms India"** — the sources Sonar read were SourceForge, IndiaAI,
  Syddhi and Yotta Shakti Cloud. simplismart.ai wasn't among the pages it consulted.
- Competitors fluctuate run to run (Fireworks 3/8 to 2/8, Together 2/8 to 1/8). We're
  flat at the floor. That consistency is the finding.

## Blockers

- **Google changed the Gemini key format** (`AIza` to `AQ.`) mid-2026; docs still show
  the old one. ~20 min lost.
- **Exhausted Gemini's free tier** (~250 req/day). I chose not to rotate keys to evade
  it. Instead the tool degrades honestly: failures are logged, and the report shows `?`
  for unknown rather than counting a failed query as "not mentioned." One run reads
  `0/8 queries succeeded` rather than showing five brands at a fake 0%.
- **OpenAI was my first pick for provider two** — code written and correct
  (`openai_test.py`, Responses API + `web_search`), blocked on `insufficient_quota`. New
  accounts get no free credit. Switched to Sonar.
- **Gemini returns citations as `vertexaisearch` redirects**, not real domains, so
  domain-level matching only works on Sonar.

## Tradeoffs

- **n=1 per query.** Biggest limitation, and I measured it: two runs 7 minutes apart
  disagreed on q4. Single samples are directional, not precise.
- **Regex detection, not an LLM judge.** Deterministic and testable, but can't catch
  paraphrase. Tests cover the traps — "multimodal" isn't Modal, "working together" isn't
  Together AI, and real output contained "Firework AI" singular.
- **CLI over dashboard.** Spent that time on the second provider and on failure handling,
  which change whether the numbers are trustworthy.
- **No scheduling.** Runs are manual.

## Next week

1. **k=3-5 sampling** per query, reporting mention *rate* — fixes the noise.
2. **The other two engines** so all four in the brief are covered.
3. **Scheduled runs** via GitHub Actions with a Slack alert on threshold moves.
4. **Aggregate the cited domains.** Not just "were we mentioned" but which pages the
   engines read. No vendor homepage was ever cited — only third-party listicles and
   competitors' comparison guides. That turns the tracker from a scoreboard into a
   target list.
