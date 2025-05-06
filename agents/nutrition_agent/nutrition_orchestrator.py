import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
 
from typing import TypedDict, Annotated, Optional, List
import operator
from functools import partial
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from langchain_core.agents import AgentAction
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
 
from agents.nutrition_agent.get_user_condition_tool import get_user_condition
from agents.nutrition_agent.recommend_recipes_tool import recommend_recipes_tool
 
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
 
# ========= LangGraph State =========
class NutritionState(TypedDict):
    input: str
    username: str
    cuisine_types: List[str]
    meal_types: List[str]
    chat_history: list[BaseMessage]
    chronic_condition: Optional[str]
    intermediate_steps: Annotated[List[AgentAction], operator.add]
 
# ========= Tool Mapping =========
TOOL_MAP = {
    "get_user_condition": get_user_condition,
    "recommend_recipes": recommend_recipes_tool,
}
 
# ========= Oracle Agent =========
def init_nutrition_oracle():
    system_prompt = """
You are a structured nutrition assistant helping users with chronic conditions.
 
Strictly follow this tool sequence:
1. `get_user_condition`
2. `recommend_recipes`
 
Use only ONE tool at a time.
Never repeat or skip.
Stop after both tools are used.
Always consider previous context (scratchpad).
"""
 
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        ("assistant", "scratchpad: {scratchpad}"),
    ])
 
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)
 
    def create_scratchpad(intermediate_steps: List[AgentAction]):
        recent_steps = intermediate_steps[-4:]
        return "\n---\n".join(
            f"Tool: {step.tool}, Input: {step.tool_input}\nOutput: {step.log}"
            for step in recent_steps if step.log != "TBD"
        )
 
    return (
        {
            "input": lambda x: x["input"],
            "chat_history": lambda x: x["chat_history"],
            "scratchpad": lambda x: create_scratchpad(x["intermediate_steps"])
        }
        | prompt
        | llm.bind_tools(list(TOOL_MAP.values()), tool_choice="any")
    )
 
# ========= Oracle Executor =========
def run_nutrition_oracle(state: NutritionState, oracle) -> NutritionState:
    print("\n🧠 [Oracle] Deciding next nutrition tool...")
 
    # ✅ Stop after recommend_recipes if it succeeded
    if state["intermediate_steps"]:
        last = state["intermediate_steps"][-1]
        if last.tool == "recommend_recipes" and "❌" not in last.log and "no suitable recipes" not in last.log.lower():
            print("✅ Recommendation already successful. No further tool needed.")
            return state
 
    # ⛔ Inject recommend_recipes if chronic condition is already retrieved
    if state.get("chronic_condition") and any(
        step.tool == "get_user_condition" for step in state["intermediate_steps"]
    ):
        print("🛑 Already retrieved chronic_condition. Skipping to recommend_recipes.")
        next_action = AgentAction(
            tool="recommend_recipes",
            tool_input={
                "username": state["username"],
                "cuisine_types": state["cuisine_types"],
                "meal_types": state["meal_types"],
                "chronic_condition": state["chronic_condition"]
            },
            log="TBD"
        )
        return {**state, "intermediate_steps": state["intermediate_steps"] + [next_action]}
 
    try:
        response = oracle.invoke(state)
        print(f"🔮 Oracle tool call: {response.tool_calls}")
 
        if not response.tool_calls:
            print("⚠️ No tool call. Defaulting to get_user_condition.")
            tool_name = "get_user_condition"
            tool_args = {"username": state["username"]}
        else:
            tool_name = response.tool_calls[0]["name"]
            tool_args = response.tool_calls[0]["args"]
 
        tool_args["username"] = state["username"]
        tool_args.setdefault("cuisine_types", state["cuisine_types"])
        tool_args.setdefault("meal_types", state["meal_types"])
 
        if tool_name == "recommend_recipes":
            tool_args.setdefault("chronic_condition", state.get("chronic_condition"))
 
        print(f"🧭 Oracle chose tool: {tool_name} | Args: {tool_args}")
        action = AgentAction(tool=tool_name, tool_input=tool_args, log="TBD")
 
        if state["intermediate_steps"] and state["intermediate_steps"][-1].log == "TBD":
            print("⏩ Previous step in progress. Skipping.")
            return state
 
        return {**state, "intermediate_steps": state["intermediate_steps"] + [action]}
 
    except Exception as e:
        print(f"❌ Oracle error: {e}")
        fallback = AgentAction(tool="get_user_condition", tool_input={"username": state["username"]}, log="TBD")
        return {**state, "intermediate_steps": state["intermediate_steps"] + [fallback]}
 
 
# ========= Router =========
def route(state: NutritionState):
    print("🔀 Routing decision...")
    if not state["intermediate_steps"]:
        print("🟢 Starting fresh → get_user_condition")
        return "get_user_condition"
 
    last = state["intermediate_steps"][-1]
 
    if last.log == "TBD":
        print(f"⏳ Still waiting on: {last.tool}")
        return last.tool
 
    if last.tool == "recommend_recipes":
        if "❌" in last.log or "no suitable recipes" in last.log.lower():
            print("🛑 No recipes or error in recommendation. Stopping.")
        else:
            print("✅ Recipes fetched successfully. Stopping.")
        return END
 
    if last.tool == "get_user_condition":
        print("➡️ Moving to recommend_recipes")
        return "recommend_recipes"
 
    print(f"⚠️ Unknown tool: {last.tool}. Stopping.")
    return END
 
 
# ========= Tool Executor =========
def run_tool(state: NutritionState) -> NutritionState:
    last_action = state["intermediate_steps"][-1]
    tool_name = last_action.tool
    tool_args = last_action.tool_input
 
    tool_args.setdefault("username", state["username"])
    if tool_name == "recommend_recipes":
        tool_args.setdefault("chronic_condition", state.get("chronic_condition"))
 
    print(f"\n🔧 Executing tool: {tool_name} | Args: {tool_args}")
    print(f"📦 Current condition: {state.get('chronic_condition')}")
 
    try:
        output = TOOL_MAP[tool_name].invoke(tool_args)
        print(f"✅ Output: {str(output)[:250]}...")
        updated_state = {**state}
 
        if tool_name == "get_user_condition" and "User not found" not in str(output):
            updated_state["chronic_condition"] = str(output)
 
        updated_steps = state["intermediate_steps"][:-1] + [
            AgentAction(tool=tool_name, tool_input=tool_args, log=str(output))
        ]
        updated_state["intermediate_steps"] = updated_steps
        return updated_state
 
    except Exception as e:
        print(f"❌ Tool error: {e}")
        updated_steps = state["intermediate_steps"][:-1] + [
            AgentAction(tool=tool_name, tool_input=tool_args, log=f"Error: {str(e)}")
        ]
        return {**state, "intermediate_steps": updated_steps}
 
# ========= Build LangGraph =========
def create_nutrition_graph():
    oracle = init_nutrition_oracle()
    graph = StateGraph(NutritionState)
 
    graph.add_node("oracle", partial(run_nutrition_oracle, oracle=oracle))
    for name in TOOL_MAP:
        graph.add_node(name, run_tool)
 
    graph.set_entry_point("oracle")
    graph.add_conditional_edges("oracle", route)
    for name in TOOL_MAP:
        graph.add_edge(name, "oracle")
 
    return graph.compile()
 
# ========= Entry Point =========
nutrition_graph = create_nutrition_graph()
 
def run_nutrition_agents(input_text: str, username: str, cuisine_types: List[str], meal_types: List[str], chat_history: list[BaseMessage]) -> str:
    print("\n🚀 [run_nutrition_agents] Triggered")
    initial_state: NutritionState = {
        "input": input_text,
        "username": username,
        "cuisine_types": cuisine_types,
        "meal_types": meal_types,
        "chat_history": chat_history,
        "chronic_condition": None,
        "intermediate_steps": []
    }
 
    print(f"🧾 Initial State: {initial_state}")
    result = nutrition_graph.invoke(initial_state)
    final_output = result["intermediate_steps"][-1].log
    print(f"🎯 Final Output: {final_output[:300]}...\n")
    return final_output