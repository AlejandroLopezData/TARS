import sys
import os
from typing import TypedDict, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../system_productivity")))

from langgraph.graph import StateGraph, END

from llm import ask_llm
from prompt import build_system_prompt
from automation_router import execute_automation
from plugin_loader import discover_agents


class RouterState(TypedDict):
    user_input: str
    history: list
    action: Optional[str]
    params: Optional[dict]
    reply: Optional[str]
    result: Optional[str]


def think_node(state: RouterState) -> RouterState:
    agents = discover_agents()
    system_prompt = build_system_prompt(agents)

    parsed = ask_llm(system_prompt, state["user_input"], state.get("history", []))

    state["action"] = parsed["action"]
    state["params"] = parsed["params"]
    state["reply"] = parsed["reply"]

    return state


def route_decision(state: RouterState) -> str:
    action = state["action"]

    if action == "chat":
        return "chat_node"
    elif action == "activate_agent":
        return "agent_node"
    else:
        return "execute_node"


def execute_node(state: RouterState) -> RouterState:
    result = execute_automation(state["action"], state["params"])
    state["result"] = result
    return state


def agent_node(state: RouterState) -> RouterState:
    agents = discover_agents()
    agent_name = state["params"].get("agent_name", "")
    task = state["params"].get("task", state["user_input"])

    agent = agents.get(agent_name)

    if not agent:
        state["result"] = f"No expert agent named '{agent_name}' is available."
        return state

    state["result"] = agent["run"](task, state.get("history", []))
    return state


def chat_node(state: RouterState) -> RouterState:
    state["result"] = state["reply"]
    return state


def build_graph():
    graph = StateGraph(RouterState)

    graph.add_node("think_node", think_node)
    graph.add_node("execute_node", execute_node)
    graph.add_node("agent_node", agent_node)
    graph.add_node("chat_node", chat_node)

    graph.set_entry_point("think_node")

    graph.add_conditional_edges(
        "think_node",
        route_decision,
        {
            "execute_node": "execute_node",
            "agent_node": "agent_node",
            "chat_node": "chat_node",
        }
    )

    graph.add_edge("execute_node", END)
    graph.add_edge("agent_node", END)
    graph.add_edge("chat_node", END)

    return graph.compile()


def run_router(user_input: str, history: list = None) -> RouterState:
    app = build_graph()
    initial_state = {
        "user_input": user_input,
        "history": history or [],
        "action": None,
        "params": None,
        "reply": None,
        "result": None
    }
    return app.invoke(initial_state)