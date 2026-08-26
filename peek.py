import warnings, os, json
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"],
                base_url="https://openrouter.ai/api/v1")

r = client.chat.completions.create(
    model="perplexity/sonar",
    max_tokens=300,
    messages=[{"role": "user", "content": "AI inference platforms India"}],
)

d = r.model_dump()
d["choices"][0]["message"]["content"] = "<trimmed>"
print(json.dumps(d, indent=2)[:3000])
