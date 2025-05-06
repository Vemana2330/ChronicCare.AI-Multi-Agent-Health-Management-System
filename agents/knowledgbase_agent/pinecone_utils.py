# FILE: agents/knowledgebase_agent/pinecone_utils.py

import os
from dotenv import load_dotenv
from pinecone import Pinecone

# ==== Load Environment ====
load_dotenv()

# ==== Pinecone Config ====
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("INDEX_NAME")  # e.g., "chronic-health-index"

# ==== Init Pinecone Client ====
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)


def query_chunks_from_pinecone(query_embedding, condition: str, top_k: int = 15):
    """
    Query Pinecone using a vector and filter by condition.
    
    Args:
        query_embedding (list[float]): Embedding vector
        condition (str): e.g. "Cholesterol"
        top_k (int): Number of results to retrieve

    Returns:
        List[dict]: Matching Pinecone chunks with metadata
    """
    try:
        print(f"\n🔍 Pinecone Query for condition: '{condition}', top_k={top_k}")
        print(f"🧠 Embedding vector size: {len(query_embedding)}")

        response = index.query(
            vector=query_embedding,
            top_k=top_k,
            filter={"condition": condition},
            include_metadata=True
        )

        matches = response.get("matches", [])
        print(f"✅ Pinecone returned {len(matches)} chunks.")
        
        if not matches:
            print("⚠️ Warning: No results found. Check if metadata is uploaded correctly.")
        else:
            print("🧾 Sample matched metadata:", matches[0]["metadata"] if matches[0].get("metadata") else "No metadata in match")

        return matches

    except Exception as e:
        print(f"❌ Error querying Pinecone: {e}")
        return []


def query_multiple_conditions(query_embedding, conditions: list[str], top_k: int = 15):
    """
    Query Pinecone for multiple conditions (e.g., ['CKD', 'Cholesterol']).

    Args:
        query_embedding: OpenAI embedding
        conditions: List of condition names
        top_k: Number of chunks to retrieve

    Returns:
        List of results
    """
    try:
        print(f"\n🔍 Multi-condition Pinecone Query: {conditions}, top_k={top_k}")
        print(f"🧠 Embedding vector size: {len(query_embedding)}")

        filter_query = {"condition": {"$in": conditions}}
        response = index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=filter_query,
            include_metadata=True
        )

        matches = response.get("matches", [])
        print(f"✅ Pinecone returned {len(matches)} results for multiple conditions.")
        if matches:
            print("🧾 Sample metadata:", matches[0]["metadata"] if matches[0].get("metadata") else "No metadata")

        return matches

    except Exception as e:
        print(f"❌ Error querying Pinecone (multi-condition): {e}")
        return []