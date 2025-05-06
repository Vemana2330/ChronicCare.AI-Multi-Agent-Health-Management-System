# FILE: agents/orchestrator.py

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import TypedDict, Annotated, Optional, List
import operator
from functools import partial
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from langchain_core.agents import AgentAction
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from agents.knowledgbase_agent.knowledgebase_tool import run_vector_search, run_generate_summary

# ==== Load Environment Variables ====
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ==== LangGraph State Type ====
class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    intermediate_steps: Annotated[List[AgentAction], operator.add]
    condition: Optional[str]

# ==== Tool Wrappers ====
@tool("vector_search")
def vector_search_tool(query: str, condition: str) -> str:
    """
    Answer a specific medical question using semantic search on Pinecone chunks 
    filtered by the chronic condition. Extracts context and responds to the question.
    
    Args:
        query (str): The user question.
        condition (str): The chronic condition selected by the user (e.g., "Diabetes").
    
    Returns:
        str: An answer based on the most relevant document snippets retrieved.
    """
    print(f"🛠 Running vector_search_tool with query='{query}' and condition='{condition}'")
    return run_vector_search(query, condition)


@tool("generate_summary")
def generate_summary_tool(condition: str) -> str:
    """
    Generate a complete medical summary for a chronic condition, answering:
    
    1. What is that disease?
    2. What are the symptoms?
    3. What are the stages of the condition?
    4. What are the treatments available?
    5. What are some remedies or lifestyle tips?
    6. What medications are recommended?
    7. What is the general doctor's advice?
    
    Args:
        condition (str): The chronic condition (e.g., "CKD", "Type2").
    
    Returns:
        str: A structured summary for the condition.
    """
    print(f"🛠 Running generate_summary_tool with condition='{condition}'")
    return run_generate_summary(condition)

# ==== Tool Mapping ====
TOOL_MAP = {
    "vector_search": vector_search_tool,
    "generate_summary": generate_summary_tool
}

# ==== Oracle Agent ====
def init_oracle_agent():
    system_prompt = """You are a helpful health assistant.
    
If the user asks a question like “What are the symptoms of CKD?” → use `vector_search`.  
If the user wants a complete summary → use `generate_summary`.

Rules:
- Use `vector_search` only for questions.
- Use `generate_summary` only when full summary is asked.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        ("assistant", "scratchpad: {scratchpad}"),
    ])

    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=OPENAI_API_KEY)

    def create_scratchpad(intermediate_steps: List[AgentAction]):
        return "\n---\n".join(
            f"Tool: {step.tool}, Input: {step.tool_input}\nOutput: {step.log}"
            for step in intermediate_steps if step.log != "TBD"
        )

    oracle = (
        {
            "input": lambda x: x["input"],
            "chat_history": lambda x: x["chat_history"],
            "scratchpad": lambda x: create_scratchpad(x["intermediate_steps"])
        }
        | prompt
        | llm.bind_tools([vector_search_tool, generate_summary_tool], tool_choice="any")
    )

    return oracle

# ==== Oracle Selector ====
def run_oracle(state: AgentState, oracle) -> AgentState:
    print("\n🧠 [Oracle] Deciding tool based on user input + history...")

    try:
        response = oracle.invoke(state)
        print(f"🔍 Oracle response tool call: {response.tool_calls}")

        if not response.tool_calls or len(response.tool_calls) == 0:
            print("⚠️ Oracle failed to return a valid tool, defaulting to generate_summary")
            tool_name, tool_args = "generate_summary", {"condition": state.get("condition")}
        else:
            tool_name = response.tool_calls[0]["name"]
            tool_args = response.tool_calls[0]["args"]

        action = AgentAction(tool=tool_name, tool_input=tool_args, log="TBD")
        print(f"🧭 Oracle chose tool: {tool_name} | Args: {tool_args}")

        return {
            **state,
            "intermediate_steps": [action]
        }

    except Exception as e:
        print(f"❌ Error in run_oracle: {str(e)}")
        fallback = AgentAction(tool="generate_summary", tool_input={"condition": state.get("condition")}, log="TBD")
        return {
            **state,
            "intermediate_steps": [fallback]
        }

# ==== Router ====
def route(state: AgentState):
    print("🔀 Routing decision based on current tool step...")
    if not state["intermediate_steps"]:
        print("⚠️ No previous steps, routing to generate_summary")
        return "generate_summary"

    last_step = state["intermediate_steps"][-1]

    if last_step.log != "TBD":
        print(f"✅ Tool already completed. Stopping. Tool: {last_step.tool}")
        return END

    print(f"➡️ Routing to tool: {last_step.tool}")
    return last_step.tool

# ==== Tool Execution ====
def run_tool(state: AgentState) -> AgentState:
    last_action = state["intermediate_steps"][-1]
    tool_name = last_action.tool
    tool_args = last_action.tool_input

    if "condition" not in tool_args:
        tool_args["condition"] = state.get("condition")

    print(f"\n🛠 Executing tool: {tool_name} with args: {tool_args}")
    try:
        output = TOOL_MAP[tool_name].invoke(tool_args)
        print(f"✅ Tool output (truncated): {str(output)[:250]}...\n")

        action_out = AgentAction(tool=tool_name, tool_input=tool_args, log=str(output))
        return {
            **state,
            "intermediate_steps": [action_out]
        }

    except Exception as e:
        print(f"❌ Error running tool '{tool_name}': {e}")
        error_msg = f"Tool '{tool_name}' failed with: {str(e)}"
        action_out = AgentAction(tool=tool_name, tool_input=tool_args, log=error_msg)
        return {
            **state,
            "intermediate_steps": [action_out]
        }

# ==== Build LangGraph DAG ====
def create_graph():
    oracle_agent = init_oracle_agent()
    graph = StateGraph(AgentState)

    graph.add_node("oracle", partial(run_oracle, oracle=oracle_agent))
    graph.add_node("vector_search", run_tool)
    graph.add_node("generate_summary", run_tool)

    graph.set_entry_point("oracle")
    graph.add_conditional_edges("oracle", route)

    graph.add_edge("vector_search", END)
    graph.add_edge("generate_summary", END)

    return graph.compile()

# ==== Entry Point for FastAPI ====
graph_app = create_graph()

def run_agents(input_text: str, chat_history: list[BaseMessage], condition: str) -> str:
    print("\n🚀 Triggering run_agents()")
    initial_state: AgentState = {
        "input": input_text,
        "chat_history": chat_history,
        "intermediate_steps": [],
        "condition": condition
    }

    result = graph_app.invoke(initial_state)
    final_log = result["intermediate_steps"][-1].log
    print(f"🎯 Final Result: {final_log[:200]}...\n")
    return final_log
