from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Any
import os
import re
from dotenv import load_dotenv

load_dotenv()

SYNTHESIZER_SYSTEM_PROMPT = """You are NEXUS, an expert autonomous AI agent. Your job is to synthesize results from multiple tool executions into a perfect final answer.

RULES:
1. Combine ALL tool results into one comprehensive coherent response
2. Never say "I used tool X" — just present findings naturally
3. Always use markdown formatting
4. Use ## headers, **bold**, bullet points
5. End EVERY response with:
   ## ✅ Key Takeaways
   - 3-5 bullet points of most important findings
6. Be comprehensive — never give short vague answers
"""


def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=0.4,
        max_tokens=4096
    )


def extract_topic(task: str) -> str:
    """Extract clean short topic from task for image/video search."""
    topic = task.lower()
    topic = re.sub(
        r'^(what is|what are|how does|how do|explain|tell me about|'
        r'search for|find|calculate|write|create|generate|describe|'
        r'who is|why is|when is|give me|show me)',
        '', topic
    )
    topic = topic.strip()
    words = topic.split()[:4]
    topic = ' '.join(words)
    topic = re.sub(r'[^\w\s]', '', topic).strip()
    return topic if topic else task[:30]


def get_media_resources(task: str) -> Dict[str, Any]:
    """
    Generate YouTube and image resources for a task.
    No API keys needed.
    """
    topic = extract_topic(task)
    query = topic.replace(' ', '+')

    # YouTube search URL
    youtube_url = f"https://www.youtube.com/results?search_query={query}+explained"

    # Working placeholder images with topic text
    images = [
        f"https://placehold.co/400x250/1e1e3f/a5b4fc?text={query}",
        f"https://placehold.co/400x250/0f2a1a/10b981?text={query}+Overview",
        f"https://placehold.co/400x250/2a0f0f/ef4444?text={query}+Details",
    ]

    # Bing image search link
    bing_images_url = f"https://www.bing.com/images/search?q={query}"

    return {
        "topic": topic,
        "youtube_url": youtube_url,
        "youtube_label": f"Watch '{topic}' videos on YouTube",
        "images": images,
        "bing_images_url": bing_images_url
    }


def synthesize_results(
    original_task: str,
    subtasks: List[Dict[str, Any]],
    tool_results: List[Dict[str, Any]],
    memory_context: str = ""
) -> str:
    try:
        llm = get_llm()
        results_text = build_results_context(subtasks, tool_results)

        user_message = f"""Original Task: {original_task}

Tool Execution Results:
{results_text}
"""
        if memory_context:
            user_message += f"\nPrevious Conversation:\n{memory_context}\n"

        user_message += "\nSynthesize into a comprehensive final answer with markdown formatting and Key Takeaways."

        messages = [
            SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ]

        response = llm.invoke(messages)
        return response.content.strip()

    except Exception as e:
        return fallback_synthesis(original_task, tool_results)


def build_results_context(
    subtasks: List[Dict[str, Any]],
    tool_results: List[Dict[str, Any]]
) -> str:
    lines = []
    for i, result in enumerate(tool_results):
        tool = result.get("tool", "unknown")
        output = result.get("output", "No output")
        success = result.get("success", False)
        description = result.get("description", "")
        status = "✓ SUCCESS" if success else "✗ FAILED"
        lines.append(f"--- Step {i+1}: {tool.upper()} ({status}) ---")
        lines.append(f"Task: {description}")
        lines.append(f"Result: {str(output)[:1500]}")
        lines.append("")
    return "\n".join(lines)


def fallback_synthesis(task: str, tool_results: List[Dict[str, Any]]) -> str:
    lines = [f"## Results for: {task}\n"]
    for i, result in enumerate(tool_results):
        tool = result.get("tool", "unknown")
        output = result.get("output", "No output")
        success = result.get("success", False)
        status = "✅" if success else "❌"
        lines.append(f"### {status} Step {i+1} — {tool.upper()}")
        lines.append(str(output)[:800])
        lines.append("")
    if not tool_results:
        lines.append("No results were generated.")
    return "\n".join(lines)


def generate_confidence_score(tool_results: List[Dict[str, Any]]) -> float:
    if not tool_results:
        return 0.0
    successful = sum(1 for r in tool_results if r.get("success", False))
    base_score = successful / len(tool_results)
    tool_bonus = min(len(tool_results) * 0.05, 0.2)
    return min(round(base_score + tool_bonus, 2), 1.0)