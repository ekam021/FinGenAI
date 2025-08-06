# modules/pdf_qa_bot.py

import os
import requests
import re
from rapidfuzz import fuzz
from modules.retriever import retrieve_top_chunks

# === Groq Configuration ===
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")

# === Utility ===
def extract_company_name(query):
    match = re.search(r"(Nestlé[\w\s\.\-]+)", query, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def fuzzy_contains(target, source, threshold=85):
    return fuzz.partial_ratio(target.lower(), source.lower()) >= threshold

# === Prompt Builder ===
def build_prompt(query: str, chunks: list) -> str:
    query_lower = query.lower()
    matched_chunks = []

    for i, chunk in enumerate(chunks):
        text = chunk.get("text", "").lower()
        table = chunk.get("table_text", "").lower()
        combined = f"{text} {table}".strip()

        if all(term in combined for term in query_lower.split() if term not in ['what', 'are', 'the', 'is', 'in', 'of', 'as', 'at']):
            matched_chunks.append(chunk)

    if not matched_chunks:
        return "No relevant information found."

    context_blocks = []
    for chunk in matched_chunks:
        context_blocks.append("\n".join(
            filter(None, [chunk.get("text", ""), chunk.get("table_text", "")])
        ))

    context = "\n\n".join(context_blocks)

    return f"""
You are a highly accurate financial assistant designed to answer questions based strictly on the content of uploaded financial PDF documents.

Instructions:
1. Use **only exact data** from the PDFs.
2. Extract rows that match **country, term, and year** exactly.
3. If answer is not explicitly present, respond with: **"Information not provided."**
4. If the year is not specified in the query and the information is provided for multiple 
    years then respond with all the years.
5. Highlight the final answer like this: **Answer:** 29 million CHF (2024)
6. And write the answers in a structured format **bulleted points**, **one below the other**.

Context:
{context}

Question: {query}

Answer:
"""


# === Groq Query Function ===
def generate_answer(query: str, chunks: list) -> str:
    prompt = build_prompt(query, chunks)

    #print(f"[DEBUG] Prompt length: {len(prompt)} characters")

    if prompt.strip() == "No relevant information found.":
      #  print("[DEBUG] ❌ No relevant chunks matched entity.")
        return "Information not provided."

    #print("[DEBUG] 🤖 Sending prompt to Groq...")
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
        )

        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            #print(f"[DEBUG] ✅ Groq Response:\n{answer}\n")

            return answer.strip()
        else:
            print(f"[ERROR] Groq API Status: {response.status_code}")
            print(f"[ERROR] Groq API Response: {response.text}")

            return "❌ Groq API Error: Unable to retrieve answer."

    except Exception as e:
        print(f"[ERROR] Groq call failed: {e}")
        return "❌ Failed to generate answer from Groq."

# === Main Question Handler ===
def ask_pdf_question(query: str, file_hash: str) -> str:
    chunks = retrieve_top_chunks(query, file_hash)

    if not chunks:
        return "❌ No relevant content found in Pinecone index."

    #print(f"[DEBUG] Retrieved {len(chunks)} chunks for query: {query}")
    #for i, c in enumerate(chunks):
     #   print(f"[CHUNK DEBUG] Chunk {i+1}:\nText: {c.get('text', '')[:300]}\nTable: {c.get('table_text', '')[:300]}\n")


    return generate_answer(query, chunks)
