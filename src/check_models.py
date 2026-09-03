import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])
models = client.models.list()

print("Available models for your account:")
for m in models.data:
    print(f" - {m.id}")