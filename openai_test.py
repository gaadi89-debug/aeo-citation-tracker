import warnings
warnings.filterwarnings("ignore")

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

r = client.responses.create(
    model="gpt-5",
    input="Best AI inference infrastructure platforms for production deployment",
    tools=[{"type": "web_search"}],
)

print(r.output_text)
print()
print("--- CITATIONS ---")
for item in r.output:
    if item.type == "message":
        for c in item.content:
            for ann in getattr(c, "annotations", []) or []:
                if ann.type == "url_citation":
                    print(ann.url[:90])
