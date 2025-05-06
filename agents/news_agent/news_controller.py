# src/agents/web_agent/news_controller.py

import os
import logging
from typing import Literal, Dict, Any
from langgraph.graph import END, StateGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from agents.news_agent.news_tool import get_latest_news

# === Load environment variables ===
load_dotenv()

# === Logging setup ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# === State Definition ===
class NewsAgentState(Dict[str, Any]):
    chronic_condition: str
    news_results: Dict[str, Any]
    next_step: str

# === Oracle Node ===
def run_oracle(state: NewsAgentState) -> NewsAgentState:
    try:
        condition = state.get("chronic_condition", "").strip()
        logger.info(f"[🔀 Oracle] Received condition: {condition}")

        # Proper prompt template with variable substitution
        prompt = ChatPromptTemplate.from_template(
            """You are an intelligent router for a health news agent.
The user is asking for updates about the following chronic condition: {chronic_condition}.
If the condition is valid and specific, respond with: {{ "decision": "get_news" }}
If the condition is vague or unsupported, respond with: {{ "decision": "end" }}
Return only the JSON with the key "decision"."""
        )

        # Tool schema for structured JSON output
        function_def = {
            "name": "route_decision",
            "description": "Decides if news should be fetched for the condition.",
            "parameters": {
                "type": "object",
                "properties": {
                    "decision": {
                        "type": "string",
                        "enum": ["get_news", "end"]
                    }
                },
                "required": ["decision"]
            }
        }

        # LLM setup (no function call, just structured output)
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Use structured output mode instead of bind_tools
        chain = prompt | llm.with_structured_output(function_def)

        result = chain.invoke({"chronic_condition": condition})
        decision = result.get("decision", "end")

        logger.info(f"[🔀 Oracle Decision] → {decision}")
        return {
            **state,
            "next_step": decision
        }

    except Exception as e:
        logger.error(f"[❌ Oracle Error] {str(e)}")
        return {**state, "next_step": "end"}

# === News Fetch Node ===
def run_get_news(state: NewsAgentState) -> NewsAgentState:
    condition = state.get("chronic_condition", "").strip()
    logger.info(f"[📡 Fetching News] For condition: {condition}")

    try:
        news = get_latest_news(condition)

        if "error" in news:
            logger.warning(f"[⚠️ News Fetch Returned Error] {news['error']}")
        else:
            logger.info(f"[✅ News Fetch Successful] {news['total_results']} articles retrieved.")

        return {
            **state,
            "news_results": news,
            "next_step": "end"
        }

    except Exception as e:
        logger.error(f"[❌ Fetch Error] {str(e)}")
        return {
            **state,
            "news_results": {"error": f"Failed to fetch news: {str(e)}"},
            "next_step": "end"
        }

# === LangGraph Decision Router ===
def decide_next(state: NewsAgentState) -> Literal["get_news", "end"]:
    return state.get("next_step", "end")

# === Build LangGraph ===
def create_news_agent_graph() -> StateGraph:
    graph = StateGraph(NewsAgentState)
    graph.add_node("oracle", run_oracle)
    graph.add_node("get_news", run_get_news)

    graph.set_entry_point("oracle")

    graph.add_conditional_edges(
        "oracle",
        decide_next,
        {
            "get_news": "get_news",
            "end": END
        }
    )

    graph.add_edge("get_news", END)
    return graph

# === Runner Function ===
def run_news_agent(chronic_condition: str) -> Dict[str, Any]:
    graph = create_news_agent_graph()
    app = graph.compile()

    initial_state = {
        "chronic_condition": chronic_condition,
        "news_results": {},
        "next_step": "oracle"
    }

    logger.info(f"[🚀 News Agent Invoked] for '{chronic_condition}'")
    final_state = app.invoke(initial_state)

    if "news_results" not in final_state:
        logger.warning("[⚠️ No news_results found in final_state]")
        return {"error": "No results returned"}

    return final_state["news_results"]
