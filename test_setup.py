# test_setup.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load your API keys from .env
load_dotenv()

# Test Gemini connection
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")
response = model.generate_content("Say hello in one sentence.")

print("✅ Gemini connected!")
print("Response:", response.text)