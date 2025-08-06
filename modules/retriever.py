from modules.pinecone_handler import query_pinecone_index

TOP_K = 20  # Customize as needed

# modules/retriever.py


def retrieve_top_chunks(query: str, file_hash: str) -> list:
    #print(f"[DEBUG] 🔍 Querying Pinecone with file_hash: {file_hash}")

    try:
        response = query_pinecone_index(query_text=query, top_k=TOP_K, namespace=file_hash)

        if not response or not response.matches:
            print("[DEBUG] ❌ No matches found.")
            return []

       # print(f"[DEBUG] ✅ Matches found: {len(response.matches)}")

        results = []

        for i, match in enumerate(response.matches):
            metadata = match.metadata or {}

            text = metadata.get("text", "").strip()
            table_text = metadata.get("table_text", "").strip()
            page = metadata.get("page_number", "N/A")

           # print(f"[CHUNK DEBUG] Match {i+1}")
            #print(f"📄 Page: {page}")
            #print(f"📊 Score: {match.score:.4f}")
            #print(f"📄 Text Snippet: {text[:100]}")
            #print(f"📄 Table Snippet: {table_text[:100]}")

            if text or table_text:  # ✅ Only append if useful
                results.append({
                    "text": text,
                    "table_text": table_text,
                    "metadata": metadata
                })

        if not results:
            print("[DEBUG] ❌ All chunks were empty or filtered out.")
        #else:
         #   print(f"[DEBUG] ✅ Final chunks to use: {len(results)}")

        return results

    except Exception as e:
        print(f"[ERROR] ❌ Pinecone query failed: {e}")
        return []
