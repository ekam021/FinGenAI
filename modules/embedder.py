# modules/embedder.py
import os
import hashlib
import pickle
import faiss
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def compute_file_hash(filepath):
    with open(filepath, "rb") as f:
        bytes = f.read()
        return hashlib.sha256(bytes).hexdigest()

def embed_chunks(chunks, file_hash):
    texts = [chunk.get("table_text", "") or chunk.get("text", "") for chunk in chunks]
    embeddings = model.encode(texts, convert_to_numpy=True)

    # Attach metadata to each embedding
    metadata = []
    for i, chunk in enumerate(chunks):
        metadata.append({
            "text": texts[i],
            "source": chunk.get("source", ""),
            "page_number": chunk.get("page_number", -1),
            "row_index": chunk.get("row_index", -1),
            "file_hash": file_hash
        })

    return embeddings, metadata


def build_faiss_index(chunks, file_hash):
    index_path = f"indices/{file_hash}.index"
    metadata_path = f"indices/{file_hash}_metadata.pkl"

    if os.path.exists(index_path) and os.path.exists(metadata_path):
        print(f"[CACHED] 🔁 Loading index for {file_hash}")
        index = faiss.read_index(index_path)
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
        return index, metadata

    print(f"[PROCESSING] 🔄 Building index for {file_hash}")
    embeddings = embed_chunks(chunks)

    if embeddings.shape[0] == 0:
        raise ValueError("No embeddings generated.")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    with open(metadata_path, "wb") as f:
        pickle.dump(chunks, f)
    faiss.write_index(index, index_path)

    return index, chunks




