# FILE: agents/knowledgebase_agent/knowledgebase_tool.py

import sys
import os
from typing import List
from dotenv import load_dotenv
import tiktoken
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from agents.knowledgbase_agent.pinecone_utils import query_chunks_from_pinecone

# ==== Path and Environment Setup ====
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
embeddings_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)

# ==== GPT Token Management ====
encoding = tiktoken.encoding_for_model("gpt-4o-mini")

def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

def truncate_chunks(chunks: List[str], max_tokens: int = 8000) -> str:
    total = 0
    final = []
    for chunk in chunks:
        tokens = count_tokens(chunk)
        if total + tokens > max_tokens:
            print(f"⚠️ Stopping truncation at token count {total} (limit: {max_tokens})")
            break
        final.append(chunk)
        total += tokens
    print(f"🧮 Truncated to {len(final)} chunks with total tokens = {total}")
    return "\n\n".join(final)

# ==== Summary Questions ====
SUMMARY_QUESTIONS = [
    "What is that disease?",
    "What are the symptoms?",
    "What are the stages of the condition?",
    "What are the treatments available?",
    "What are some remedies or lifestyle tips?",
    "What medications are recommended?",
    "What is the general doctor's advice?"
]

# ==== Core Vector Search Logic ====
def run_vector_search(query: str, condition: str) -> str:
    print(f"\n🔍 Running vector_search → Query: '{query}', Condition: '{condition}'")

    try:
        query_vector = embeddings_model.embed_query(query)
        print("✅ Generated query embedding.")

        results = query_chunks_from_pinecone(query_vector, condition=condition)
        if not results:
            print("⚠️ No results found in Pinecone for this condition.")
            return "No relevant information found for this condition."

        context = "\n\n".join([match["metadata"]["text"] for match in results])
        print(f"📚 Total chunks retrieved: {len(results)}, Token estimate: {count_tokens(context)}")

        prompt = f"""Use the following context to answer the question:\n\n{context}\n\nQuestion: {query}"""
        answer = llm.invoke(prompt)
        response_text = answer.content.strip() if answer else "No answer generated."

        print("💬 LLM response complete.")
        return response_text

    except Exception as e:
        print(f"❌ Error in run_vector_search: {str(e)}")
        return f"❌ Error in run_vector_search: {str(e)}"


# ==== Summary Generator Logic ====
def run_generate_summary(condition: str) -> str:
    print(f"\n📄 Generating summary for condition: '{condition}'")

    try:
        query_vector = embeddings_model.embed_query(condition)
        print("✅ Created embedding for condition summary.")

        results = query_chunks_from_pinecone(query_vector, condition=condition, top_k=50)
        if not results:
            print("⚠️ No data found in Pinecone for summary.")
            return "No data found for summary."

        all_chunks = [match["metadata"]["text"] for match in results]
        print(f"📚 Retrieved {len(all_chunks)} chunks before truncation.")

        context = truncate_chunks(all_chunks, max_tokens=8000)

        full_summary = ""
        for idx, question in enumerate(SUMMARY_QUESTIONS, 1):
            print(f"\n❓ [{idx}/{len(SUMMARY_QUESTIONS)}] Question: {question}")
            prompt = f"""Using the following medical context, answer this question:\n\n{question}\n\nContext:\n{context}"""

            response = llm.invoke(prompt)
            answer = response.content.strip() if response else "No answer generated."

            full_summary += f"### {question}\n{answer}\n\n"
            print(f"✅ Answer complete. Tokens used: {count_tokens(answer)}")

        print("\n🧾 Summary generation complete.")
        return full_summary.strip()

    except Exception as e:
        print(f"❌ Error in run_generate_summary: {str(e)}")
        return f"❌ Error in run_generate_summary: {str(e)}"
