import os
from dotenv import load_dotenv
import groq



#  Load the .env file
dotenv_loaded = load_dotenv()
print(" .env loaded:", dotenv_loaded)

#  Read the key
api_key = os.getenv("GROQ_API_KEY")


if not api_key:
    raise ValueError(" GROQ_API_KEY not found. Make sure .env file is correct and 'python-dotenv' is installed.")

print(" Loaded key starts with:", api_key[:10], "********")

#  Create client
client = groq.Groq(api_key=api_key)

def ask_finance_bot(prompt):
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a financial assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
