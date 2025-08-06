# modules/pinecone_handler.py

import os
import hashlib
from typing import List
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

# === Load env vars ===
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "fingenai-index")

# === Pinecone Init (✅ NEW SYNTAX) ===
pc = Pinecone(api_key=PINECONE_API_KEY)

if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(PINECONE_INDEX_NAME)

# === Sentence Transformer Model ===
model = SentenceTransformer("all-MiniLM-L6-v2")


# === Embedding ===
def embed_texts(texts: List[str]):
    return model.encode(texts, show_progress_bar=False).tolist()


def embed_query(query: str):
    return model.encode([query])[0].tolist()


# === File Hashing ===
def compute_file_hash(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# === Check namespace ===
def vectors_exist_in_pinecone(file_hash: str):
    try:
        stats = index.describe_index_stats()
        return file_hash in stats.namespaces and stats.namespaces[file_hash]["vector_count"] > 0
    except Exception as e:
        print(f"[ERROR] Pinecone namespace check failed: {e}")
        return False


# === Upload vectors ===
from tqdm import tqdm

def upload_embeddings_to_pinecone(file_hash: str, chunks: List[dict], batch_size: int = 100):
    vectors = []
    texts = [chunk.get("text", "") or chunk.get("table_text", "") for chunk in chunks]
    embeddings = embed_texts(texts)
   

    for i, embedding in enumerate(embeddings):
        meta = chunks[i].get("metadata", {})
        meta.update({"text": texts[i]})  # include actual text for display

        vectors.append({
            "id": f"{file_hash}_{i}",
            "values": embedding,
            "metadata": meta
        })

    #print(f"[DEBUG] Total vectors to upload: {len(vectors)}")

    # ✅ Upload in smaller batches
    for i in tqdm(range(0, len(vectors), batch_size), desc="Uploading to Pinecone"):
        batch = vectors[i:i + batch_size]
        for chunk in chunks:
            if "Nestlé Algérie SpA" in chunk.get("table_text", ""):
        # Do something
                pass

            print(f"[INDEXING] Uploading Nestlé Algérie SpA row:\n{chunk}")
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):

        #if "Nestlé Algérie SpA" in chunk.get("table_text", ""):
           # print(f"[DEBUG] ✅ Uploading to Pinecone (Page {chunk['metadata'].get('page_number')}): {chunk['table_text']}")

        try:
            index.upsert(vectors=batch, namespace=file_hash)
        except Exception as e:
            print(f"[❌ ERROR] Failed to upload batch {i}-{i + batch_size}: {e}")



# === Query ===
def query_pinecone_index(query_text, top_k=5, namespace=None):
    import numpy as np

    embedding = model.encode([query_text])[0].tolist()
    if isinstance(embedding, np.ndarray):
        embedding = embedding.tolist()

    embedding = [float(x) for x in embedding]

    try:
        query_args = {
            "vector": embedding,
            "top_k": top_k,
            "include_metadata": True
        }
        if namespace:
            query_args["namespace"] = namespace

        response = index.query(**query_args)
        return response
    except Exception as e:
        print(f"[❌ Pinecone Query Error] {e}")
        return None
