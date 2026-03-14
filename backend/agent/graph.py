import os
import time
from typing import List, Dict, Any, Optional, TypedDict
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from tools import execute_tool, get_all_tool_descriptions
from agent.planner import decompose_task, replan_after_failure, is_conversational
from agent.synthesizer import synthesize_results
from agent.memory_manager import AgentMemoryManager
from memory.episodic import save_agent_run, save_tool_call

load_dotenv()


# ─── Agent State ───────────────────────────────────────────
class AgentState(TypedDict):
    session_id: str
    task: str
    subtasks: List[Dict[str, Any]]
    current_step_index: int
    completed_steps: List[Dict[str, Any]]
    final_answer: str
    confidence: float
    tools_used: List[str]
    status: str
    error: Optional[str]
    context: str
    thoughts: List[str]
    max_iterations: int
    iterations: int


# ─── LLM ───────────────────────────────────────────────────
def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1,
        max_tokens=1024
    )


# ─── Node 1: Planner ───────────────────────────────────────
def planner_node(state: AgentState) -> AgentState:
    """Decompose the task into subtasks."""
    task = state["task"]
    context = state.get("context", "")
    thoughts = state.get("thoughts", [])

    # Get memory context
    memory = AgentMemoryManager(state["session_id"])
    full_context = memory.get_full_context(task)
    combined_context = f"{context}\n{full_context}".strip()

    thoughts.append(f"Planning task: '{task}'")

    subtasks = decompose_task(task, combined_context)

    thoughts.append(
        f"Created {len(subtasks)} subtasks: "
        + ", ".join([s.get("subtask", "")[:40] for s in subtasks])
    )

    return {
        **state,
        "subtasks": subtasks,
        "current_step_index": 0,
        "completed_steps": [],
        "tools_used": [],
        "thoughts": thoughts,
        "context": combined_context,
        "status": "executing"
    }


# ─── Node 2: Executor ──────────────────────────────────────
def executor_node(state: AgentState) -> AgentState:
    """Execute the current subtask using the assigned tool."""
    subtasks = state["subtasks"]
    index = state["current_step_index"]
    completed_steps = state.get("completed_steps", [])
    thoughts = state.get("thoughts", [])
    tools_used = state.get("tools_used", [])
    iterations = state.get("iterations", 0)

    # Check max iterations
    if iterations >= state.get("max_iterations", 10):
        thoughts.append("Max iterations reached — stopping.")
        return {
            **state,
            "status": "max_iterations_reached",
            "thoughts": thoughts
        }

    if index >= len(subtasks):
        return {**state, "status": "synthesizing"}

    current_subtask = subtasks[index]
    tool_name = current_subtask.get("tool", "web_search")
    tool_input = current_subtask.get("tool_input", state["task"])
    subtask_desc = current_subtask.get("subtask", "")

    thoughts.append(
        f"Step {index + 1}: {subtask_desc} → using '{tool_name}'"
    )

    # Execute tool
    start_time = time.time()
    result, success = execute_tool(tool_name, tool_input)
    duration = time.time() - start_time

    # Save tool call to episodic memory
    save_tool_call(
        session_id=state["session_id"],
        run_id=None,
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=result,
        success=success
    )

    if success:
        thoughts.append(f"Tool '{tool_name}' succeeded in {duration:.1f}s")
    else:
        thoughts.append(f"Tool '{tool_name}' failed: {result[:100]}")

    completed_step = {
        **current_subtask,
        "result": result,
        "success": success,
        "duration": duration
    }
    completed_steps = completed_steps + [completed_step]

    if tool_name not in tools_used:
        tools_used = tools_used + [tool_name]

    return {
        **state,
        "completed_steps": completed_steps,
        "current_step_index": index + 1,
        "tools_used": tools_used,
        "thoughts": thoughts,
        "iterations": iterations + 1,
        "status": "executing"
    }


# ─── Node 3: Reflector ─────────────────────────────────────
def reflector_node(state: AgentState) -> AgentState:
    """Check execution status and handle failures."""
    completed_steps = state.get("completed_steps", [])
    subtasks = state["subtasks"]
    index = state["current_step_index"]
    thoughts = state.get("thoughts", [])

    # Check if last step failed
    if completed_steps:
        last_step = completed_steps[-1]
        if not last_step.get("success", True):
            failure_reason = last_step.get("result", "Unknown error")
            thoughts.append("Step failed — replanning...")

            new_steps = replan_after_failure(
                original_task=state["task"],
                failed_step=last_step,
                failure_reason=failure_reason,
                completed_steps=completed_steps
            )

            remaining_subtasks = subtasks[:index] + new_steps
            return {
                **state,
                "subtasks": remaining_subtasks,
                "thoughts": thoughts,
                "status": "executing"
            }

    # Check if all steps done
    if index >= len(subtasks):
        thoughts.append(
            f"All {len(subtasks)} steps completed — synthesizing answer..."
        )
        return {**state, "thoughts": thoughts, "status": "synthesizing"}

    return {**state, "thoughts": thoughts, "status": "executing"}


# ─── Node 4: Synthesizer ───────────────────────────────────
def synthesizer_node(state: AgentState) -> AgentState:
    """Combine all results into final answer."""
    completed_steps = state.get("completed_steps", [])
    thoughts = state.get("thoughts", [])

    # Get memory context for better synthesis
    memory = AgentMemoryManager(state["session_id"])
    memory_context = memory.get_conversation_context()

    synthesis = synthesize_results(
        original_task=state["task"],
        completed_steps=completed_steps,
        context=memory_context
    )

    thoughts.append(
        f"Answer ready — {synthesis['confidence']}% confidence"
    )

    # Save to episodic memory
    save_agent_run(
        session_id=state["session_id"],
        task=state["task"],
        subtasks=[s.get("subtask", "") for s in completed_steps],
        tools_used=synthesis["tools_used"],
        final_answer=synthesis["answer"],
        confidence=synthesis["confidence"],
        duration=sum(s.get("duration", 0) for s in completed_steps),
        status="completed"
    )

    # Store answer in memory for future context
    memory.add_agent_message(synthesis["answer"])

    return {
        **state,
        "final_answer": synthesis["answer"],
        "confidence": synthesis["confidence"],
        "tools_used": synthesis["tools_used"],
        "thoughts": thoughts,
        "status": "completed"
    }


# ─── Routing Logic ─────────────────────────────────────────
def should_continue(state: AgentState) -> str:
    status = state.get("status", "executing")
    if status == "synthesizing":
        return "synthesize"
    elif status in ["completed", "max_iterations_reached"]:
        return "end"
    else:
        return "execute"


# ─── Build Graph ───────────────────────────────────────────
def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reflector", reflector_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "reflector")

    graph.add_conditional_edges(
        "reflector",
        should_continue,
        {
            "execute": "executor",
            "synthesize": "synthesizer",
            "end": END
        }
    )

    graph.add_edge("synthesizer", END)

    return graph.compile()


# ─── Main Runner ───────────────────────────────────────────
async def run_agent(
    task: str,
    session_id: str,
    context: str = "",
    on_thought=None
) -> Dict[str, Any]:
    """
    Run the agent on a task.
    on_thought: async callback for streaming thoughts.
    """
    agent = build_agent_graph()

    initial_state: AgentState = {
        "session_id": session_id,
        "task": task,
        "subtasks": [],
        "current_step_index": 0,
        "completed_steps": [],
        "final_answer": "",
        "confidence": 0.0,
        "tools_used": [],
        "status": "planning",
        "error": None,
        "context": context,
        "thoughts": [],
        "max_iterations": 10,
        "iterations": 0
    }

    try:
        final_state = await agent.ainvoke(initial_state)

        # Stream thoughts if callback provided
        if on_thought:
            for thought in final_state.get("thoughts", []):
                await on_thought(thought)

        return {
            "success": True,
            "task": task,
            "answer": final_state.get("final_answer", ""),
            "confidence": final_state.get("confidence", 0),
            "tools_used": final_state.get("tools_used", []),
            "steps": final_state.get("completed_steps", []),
            "thoughts": final_state.get("thoughts", []),
            "status": final_state.get("status", "completed")
        }

    except Exception as e:
        return {
            "success": False,
            "task": task,
            "answer": f"Agent error: {str(e)}",
            "confidence": 0,
            "tools_used": [],
            "steps": [],
            "thoughts": [f"Error: {str(e)}"],
            "status": "error"
        }