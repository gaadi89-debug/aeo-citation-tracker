# Blockers hit

1. Google migrated Gemini API key format from `AIza` to `AQ.` (June 2026).
   Most docs and SDK examples still show the old format. Cost ~20 min.

2. Gemini returns citations as `vertexaisearch.cloud.google.com` redirect
   URLs, not real domains. Matched on `chunk.web.title` instead.

3. Gemini free tier is ~10 req/min — added a 7s sleep between calls.

4. OpenAI as provider #2: code written and correct (Responses API +
   web_search tool), but the account had no credits — 429 insufficient_quota.
   New OpenAI accounts get no free tier. See openai_test.py.

# Findings so far (3 runs, Gemini grounded)

- Simplismart appears in 1/8 queries — and that one is its own brand name (q7).
- q6 "AI inference platforms India": no tracked brand appears at all.
- q8 "Baseten alternatives": Baseten, Fireworks, Together AI and Modal all
  appear. Simplismart does not.
- Runs 1 and 2 were 7 minutes apart and disagreed on q4. Single-sample
  tracking is measurably noisy; a production version would run k=3-5 per
  query and report mention rate rather than a boolean.
