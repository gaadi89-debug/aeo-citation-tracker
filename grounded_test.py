import warnings
warnings.filterwarnings("ignore")

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

QUERY = "Best AI inference infrastructure platforms for production deployment"

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=QUERY,
    config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    ),
)

print("=" * 60)
print("ANSWER:")
print("=" * 60)
print(response.text)

print()
print("=" * 60)
print("SOURCES:")
print("=" * 60)

meta = response.candidates[0].grounding_metadata
if meta and meta.grounding_chunks:
    for i, chunk in enumerate(meta.grounding_chunks, 1):
        if chunk.web:
            print(f"{i}. {chunk.web.title}")
            print(f"   {chunk.web.uri[:100]}")
else:
    print("No grounding metadata — search did not run.")

