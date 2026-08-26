import warnings
warnings.filterwarnings("ignore")

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

r = client.chat.completions.create(
    model="perplexity/sonar",
       max_tokens=1000,
 messages=[{"role": "user",
               "content": "Best AI inference infrastructure platforms for production deployment"}],
)

print(r.choices[0].message.content)
print()
print("--- CITATIONS ---")
for c in (getattr(r, "citations", None) or []):
    print(c)
