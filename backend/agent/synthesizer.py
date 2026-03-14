import os
import re
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,
        max_tokens=1024
    )


def is_conversational(task: str) -> bool:
    """Detect if task is simple conversational question."""
    conversational_keywords = [
        "what is", "what are", "who is", "who are",
        "tell me", "explain", "define", "meaning of",
        "how does", "why is", "when did", "where is",
        "hi", "hello", "hey", "thanks", "thank you",
        "what do you", "can you", "could you"
    ]
    task_lower = task.lower().strip()
    for keyword in conversational_keywords:
        if task_lower.startswith(keyword):
            return True
    return len(task.split()) < 8


def synthesize_results(
    original_task: str,
    completed_steps: List[Dict[str, Any]],
    context: str = ""
) -> Dict[str, Any]:
    llm = get_llm()

    steps_summary = []
    tools_used = []
    for step in completed_steps:
        tool = step.get("tool", "unknown")
        tools_used.append(tool)
        result = step.get("result", "No result")
        subtask = step.get("subtask", "")
        success = step.get("success", True)
        status = "SUCCESS" if success else "FAILED"
        steps_summary.append(
            f"Step {step.get('step', '?')} [{status}] — {subtask}\n"
            f"Tool: {tool}\n"
            f"Result: {str(result)[:800]}"
        )

    steps_text = "\n\n".join(steps_summary)
    conversational = is_conversational(original_task)

    if conversational:
        system_prompt = """You are NEXUS AGENT — a friendly, helpful AI assistant like ChatGPT.

STRICT RULES:
1. Give a clean, direct answer in 2-4 short paragraphs
2. NO markdown headers like ## or #
3. NO "Introduction", "Summary", "Conclusion" sections
4. NO "CONFIDENCE:" text in your response — never write this word
5. Write naturally like you are talking to a friend
6. Use bullet points ONLY if listing more than 4 items
7. Keep it concise and readable"""
    else:
        system_prompt = """You are NEXUS AGENT — a helpful AI assistant.

STRICT RULES:
1. Structure your answer clearly with short paragraphs
2. Use bullet points for lists
3. Bold important terms using **term**
4. NO markdown headers like ## or #
5. NO "CONFIDENCE:" text in your response — never write this word
6. Be thorough but readable
7. Maximum 400 words"""

    user_message = f"""Task: {original_task}

Research results:
{steps_text}

Write a clean, helpful response. DO NOT include "CONFIDENCE:" anywhere in your answer."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])

        answer = response.content.strip()

        # Aggressively strip confidence text
        answer = re.sub(r'CONFIDENCE:\s*\d+', '', answer).strip()
        answer = re.sub(r'Confidence:\s*\d+', '', answer).strip()
        answer = re.sub(r'confidence:\s*\d+', '', answer).strip()
        answer = re.sub(r'\n\s*\n\s*\n', '\n\n', answer).strip()

        # Calculate confidence internally without showing it
        successful = sum(1 for s in completed_steps if s.get("success", True))
        total = len(completed_steps)
        confidence = int((successful / total * 100)) if total > 0 else 75

        return {
            "answer": answer,
            "confidence": confidence,
            "tools_used": list(set(tools_used)),
            "steps_completed": total,
            "steps_successful": successful,
            "success": True
        }

    except Exception as e:
        fallback_parts = []
        for step in completed_steps:
            if step.get("success", True) and step.get("result"):
                fallback_parts.append(str(step["result"])[:500])

        fallback_answer = "\n\n".join(fallback_parts) if fallback_parts else "Unable to generate answer."

        return {
            "answer": fallback_answer,
            "confidence": 40,
            "tools_used": list(set(tools_used)),
            "steps_completed": len(completed_steps),
            "steps_successful": 0,
            "success": False,
            "error": str(e)
        }


def generate_report(
    task: str,
    final_answer: str,
    steps: List[Dict[str, Any]],
    confidence: float
) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("NEXUS AGENT — MISSION REPORT")
    lines.append("=" * 60)
    lines.append(f"\nTASK: {task}\n")
    lines.append(f"CONFIDENCE: {confidence}%")
    lines.append(f"STEPS EXECUTED: {len(steps)}\n")
    lines.append("-" * 40)
    lines.append("EXECUTION LOG:")
    lines.append("-" * 40)

    for step in steps:
        status = "✓" if step.get("success", True) else "✗"
        lines.append(
            f"\n[{status}] Step {step.get('step', '?')}: {step.get('subtask', '')}"
        )
        lines.append(f"    Tool: {step.get('tool', 'unknown')}")
        result_preview = str(step.get('result', ''))[:200]
        lines.append(f"    Result: {result_preview}...")

    lines.append("\n" + "-" * 40)
    lines.append("FINAL ANSWER:")
    lines.append("-" * 40)
    lines.append(f"\n{final_answer}")
    lines.append("\n" + "=" * 60)

    return "\n".join(lines)