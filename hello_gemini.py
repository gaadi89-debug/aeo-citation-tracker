import warnings
warnings.filterwarnings("ignore")

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Reply with exactly five words confirming you are working.",
)

print(response.text)
