# agents/web_agent/news_tool.py

import os
import logging
from dotenv import load_dotenv
from typing import Dict
from tavily import TavilyClient
from openai import OpenAI
from langchain.tools import tool

# === Load environment variables ===
load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === Setup logging ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# === OpenAI client ===
openai_client = OpenAI(api_key=OPENAI_API_KEY)

@tool
def get_latest_news(health_condition: str, max_results: int = 5) -> Dict:
    """
    Fetch the latest health-related news about a given chronic condition
    using Tavily API, and summarize each article using GPT.

    Args:
        health_condition (str): The chronic condition to fetch news for.
        max_results (int): Maximum number of articles to retrieve and summarize.

    Returns:
        Dict: News metadata + list of articles (with individual GPT summaries).
    """
    try:
        # === Query Tavily ===
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        query = f"latest medical news and discoveries about {health_condition}"
        logger.info(f"[🌐 Tavily Query] {query}")

        tavily_response = tavily_client.search(
            query=query,
            topic="news",
            search_depth="advanced",
            max_results=max_results,
            time_range="week"
        )

        articles = []

        # === Summarize Each Article ===
        for article in tavily_response.get("results", []):
            title = article.get("title", "Untitled")
            full_content = article.get("content", "")[:1000]  # Cap at 1000 chars
            preview = full_content[:200] + "..." if len(full_content) > 200 else full_content

            gpt_prompt = (
                f"You are a medical analyst. Summarize the article related to {health_condition} "
                f"in 2–3 concise sentences for a health-aware audience. Focus on treatments, risks, or research:\n\n"
                f"Title: {title}\n"
                f"Content: {full_content.strip()}"
            )

            try:
                logger.info(f"[🧠 GPT Summarizing] {title}")
                gpt_response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": gpt_prompt}],
                    temperature=0.5
                )
                summary = gpt_response.choices[0].message.content.strip()
                logger.info("[✅ Summary Ready]")
            except Exception as gpt_error:
                logger.warning(f"[⚠️ GPT Error] Failed to summarize: {str(gpt_error)}")
                summary = "GPT Summary not available."

            # === Append formatted article ===
            articles.append({
                "title": title,
                "source": article.get("source", "Unknown"),
                "published": article.get("published_time", "N/A"),
                "url": article.get("url"),
                "preview": preview,
                "summary": summary
            })

        return {
            "condition": health_condition,
            "total_results": len(articles),
            "articles": articles
        }

    except Exception as e:
        logger.error(f"[❌ Error] while fetching or summarizing news: {str(e)}")
        return {"error": f"Failed to fetch or summarize news: {str(e)}"}
