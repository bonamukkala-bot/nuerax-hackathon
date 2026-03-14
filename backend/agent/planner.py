import json
import re
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from tools import get_all_tool_descriptions
import os
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1,
        max_tokens=2048
    )


CONVERSATIONAL_PATTERNS = [
    "what is my", "who am i", "my name", "i am", "i'm",
    "hello", "hi ", "hey ", "thanks", "thank you",
    "how are you", "what are you", "who are you",
    "what can you do", "help me", "good morning",
    "good evening", "good night", "bye", "goodbye"
]


def is_conversational(task: str) -> bool:
    task_lower = task.lower().strip()
    for pattern in CONVERSATIONAL_PATTERNS:
        if pattern in task_lower:
            return True
    if len(task.split()) <= 5 and "?" in task:
        return True
    return False


def is_file_task(task: str) -> bool:
    file_keywords = [
        "analyze", "summarize", "read", "what does the file",
        "in the csv", "in the pdf", "uploaded", "dataset",
        "the file", "my file", "this file", "from the file"
    ]
    task_lower = task.lower()
    for keyword in file_keywords:
        if keyword in task_lower:
            return True
    return False


def decompose_task(task: str, context: str = "") -> List[Dict[str, Any]]:
    """
    Decompose task into subtasks.
    For conversational questions — answer directly from memory.
    For file tasks — use file tools.
    For research tasks — use search tools.
    """

    # Handle purely conversational questions directly
    if is_conversational(task) and not is_file_task(task):
        return [{
            "step": 1,
            "subtask": f"Answer conversationally: {task}",
            "tool": "wikipedia",
            "tool_input": task.replace("my", "").replace("?", "").strip(),
            "reason": "Simple conversational question"
        }]

    # Handle file-based tasks
    if is_file_task(task):
        return [
            {
                "step": 1,
                "subtask": f"Read and analyze the uploaded file",
                "tool": "data_analyzer",
                "tool_input": task,
                "reason": "Task involves uploaded file analysis"
            },
            {
                "step": 2,
                "subtask": f"Summarize findings from the file",
                "tool": "summarizer",
                "tool_input": task,
                "reason": "Summarize file content"
            }
        ]

    llm = get_llm()
    tool_descriptions = get_all_tool_descriptions()

    system_prompt = f"""You are an expert AI task planner. Decompose complex tasks into ordered subtasks.

{tool_descriptions}

Rules:
1. Break task into 2-4 subtasks maximum
2. Each subtask must use exactly one tool
3. Order subtasks logically
4. For simple factual questions — use only wikipedia or web_search (1 step)
5. For research tasks — use web_search first, then summarizer
6. For data tasks — use data_analyzer or file_reader
7. Return ONLY valid JSON

Output format:
[
  {{
    "step": 1,
    "subtask": "clear description",
    "tool": "tool_name",
    "tool_input": "exact input for tool",
    "reason": "why this step"
  }}
]"""

    user_message = f"""Task: {task}

Context: {context if context else "None"}

Decompose into subtasks. Return only JSON array."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])

        response_text = response.content.strip()
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            subtasks = json.loads(json_match.group())
            return subtasks
        else:
            return [{
                "step": 1,
                "subtask": task,
                "tool": "web_search",
                "tool_input": task,
                "reason": "Direct search"
            }]

    except json.JSONDecodeError:
        return [{
            "step": 1,
            "subtask": task,
            "tool": "web_search",
            "tool_input": task,
            "reason": "Fallback to search"
        }]
    except Exception as e:
        return [{
            "step": 1,
            "subtask": task,
            "tool": "web_search",
            "tool_input": task,
            "reason": f"Fallback: {str(e)}"
        }]


def replan_after_failure(
    original_task: str,
    failed_step: Dict[str, Any],
    failure_reason: str,
    completed_steps: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    llm = get_llm()
    tool_descriptions = get_all_tool_descriptions()

    completed_summary = ""
    if completed_steps:
        completed_summary = "\n".join([
            f"Step {s['step']}: {s['subtask']} → {str(s.get('result', 'done'))[:100]}"
            for s in completed_steps
        ])

    system_prompt = f"""You are an AI replanner. A step failed. Create alternative steps.

{tool_descriptions}

Return ONLY valid JSON array."""

    user_message = f"""Original task: {original_task}

Completed steps:
{completed_summary if completed_summary else "None"}

Failed step: {failed_step.get('subtask', '')}
Failed tool: {failed_step.get('tool', '')}
Reason: {failure_reason}

Create 1-2 alternative steps using different tools. Return only JSON."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])

        response_text = response.content.strip()
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return [{
                "step": len(completed_steps) + 1,
                "subtask": original_task,
                "tool": "wikipedia",
                "tool_input": original_task,
                "reason": "Fallback after failure"
            }]
    except Exception:
        return [{
            "step": len(completed_steps) + 1,
            "subtask": original_task,
            "tool": "wikipedia",
            "tool_input": original_task,
            "reason": "Emergency fallback"
        }]