from pinecone import Pinecone, ServerlessSpec
import os

PINECONE_API_KEY = "pcsk_2twbfv_HDanDRA4bhH8TAKjCiLchkNLycMowsq2HvPHpHzNkMQoxYb3uYz6AhLPEobtG2S"
PINECONE_ENVIRONMENT = "us-east-1"
PINECONE_INDEX_NAME = "fin-genai-index"

pc = Pinecone(api_key=PINECONE_API_KEY)

if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    print("Creating index...")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=PINECONE_ENVIRONMENT
        )
    )
    print("✅ Index created successfully.")
else:
    print("✅ Index already exists.")
