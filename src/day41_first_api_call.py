"""
Day 41 -- first LLM API call via Groq.
"""

import os

from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Say hello and confirm you're working, in one sentence."}],
)

print(response.choices[0].message.content)
