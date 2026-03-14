from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Any
import os
import re
from dotenv import load_dotenv

load_dotenv()

PLANNER_SYSTEM_PROMPT = """You are an expert task planner for NEXUS, an autonomous AI agent.

Your job is to break down ANY complex task into clear executable steps.

RULES:
1. Always break tasks into 2-6 specific sub-tasks
2. Each sub-task must use exactly ONE tool
3. Order sub-tasks logically — search first, then analyze, then summarize
4. Be very specific in each sub-task description
5. Return ONLY a numbered list, nothing else

AVAILABLE TOOLS:
- web_search: Search internet for current information, news, trends, facts
- wikipedia: Get detailed knowledge about topics, history, concepts, people
- calculator: Do any math, calculations, formulas, statistics
- data_analyzer: Analyze uploaded CSV/Excel files, find patterns
- file_reader: Read uploaded PDF, DOCX, image, text files
- python_repl: Execute Python code, generate data, run algorithms
- summarizer: Summarize long content, create reports, key points

FORMAT — each line must be exactly like this:
1. [TOOL: tool_name] What to do specifically

EXAMPLES:

Task: Research quantum computing and explain applications
1. [TOOL: wikipedia] Search quantum computing fundamentals and principles
2. [TOOL: web_search] Find latest quantum computing applications in 2024
3. [TOOL: summarizer] Summarize findings into clear explanation with examples

Task: Calculate compound interest and find best investment options
1. [TOOL: calculator] Calculate compound interest with given values
2. [TOOL: web_search] Search best investment options and returns in 2024
3. [TOOL: summarizer] Combine calculations and investment options into report

Task: Analyze uploaded sales data and find insights
1. [TOOL: data_analyzer] Run full EDA on uploaded dataset
2. [TOOL: python_repl] Calculate trends correlations and statistics
3. [TOOL: summarizer] Create executive summary of key findings

Task: Write Python code for fibonacci and explain it
1. [TOOL: python_repl] Write and execute fibonacci sequence code
2. [TOOL: summarizer] Explain the code logic and output clearly
"""

DIRECT_ANSWER_SYSTEM_PROMPT = """You are NEXUS, an expert autonomous AI agent with deep knowledge in all domains including:
- Programming and software development
- Artificial intelligence and machine learning
- Science, math, history, geography
- Business, finance, economics
- Writing, creativity, analysis

RULES:
1. Answer ALL questions directly, accurately and comprehensively
2. Use your training knowledge — do NOT say you need to search
3. Format responses with markdown — use headers, bullets, bold text
4. For code questions — provide complete working code with explanations
5. For concept questions — give detailed accurate explanations with examples
6. Remember the full conversation history and refer to it when relevant
7. If user introduced themselves use their name
8. Always end with actionable next steps or conclusions
9. Be confident and thorough — never give vague answers
"""

CHAT_SYSTEM_PROMPT = """You are NEXUS, a helpful friendly autonomous AI agent.

RULES:
1. For greetings and casual chat — respond warmly and naturally
2. Remember everything from conversation history
3. If user introduced themselves remember their name
4. Keep responses concise and friendly
5. Never use tools for simple conversation
"""


def get_llm(temperature=0.3):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=temperature,
        max_tokens=2048
    )


def classify_query(task: str) -> str:
    """
    Classify query into: simple_chat, direct_answer, needs_tools
    """
    task_lower = task.lower().strip()
    task_clean = re.sub(r'[^\w\s]', '', task_lower).strip()
    words = task_clean.split()

    # Simple chat patterns
    greetings = ["hi", "hello", "hey", "hii", "helo", "howdy", "sup", "hola"]
    if task_clean in greetings:
        return "simple_chat"

    intro_patterns = [
        r"^(iam|i am|i'm)\s+\w+$",
        r"^my name is\s+\w+$",
        r"^call me\s+\w+$",
    ]
    for pattern in intro_patterns:
        if re.search(pattern, task_lower):
            return "simple_chat"

    ack_words = ["thanks", "thank you", "ok", "okay", "got it", "cool",
                 "great", "nice", "awesome", "perfect", "bye", "goodbye"]
    if task_clean in ack_words:
        return "simple_chat"

    yes_no = ["yes", "no", "nope", "yep", "yeah", "sure"]
    if task_clean in yes_no:
        return "simple_chat"

    # Needs tools patterns — real-time or data-specific
    tool_patterns = [
        # Real-time info
        r"latest|recent|current|today|news|2024|2025|trending|update",
        # File operations
        r"upload|csv|excel|pdf|dataset|file|document|image",
        # Calculations with specific numbers
        r"\d+.*(%|percent|interest|roi|profit|loss|calculate|compute)",
        # Specific data lookups
        r"stock|price|weather|score|result|live",
    ]
    for pattern in tool_patterns:
        if re.search(pattern, task_lower):
            return "needs_tools"

    # If 3 words or less with no question — simple chat
    if len(words) <= 3:
        question_starters = ["what", "how", "why", "when", "where", "who",
                             "which", "explain", "tell", "describe", "define"]
        if not any(w in words for w in question_starters):
            return "simple_chat"

    # Everything else — direct answer from LLM knowledge
    return "direct_answer"


def is_simple_conversation(task: str) -> bool:
    return classify_query(task) == "simple_chat"


def needs_tools(task: str) -> bool:
    return classify_query(task) == "needs_tools"


def get_direct_response(task: str, conversation_history: str = "") -> str:
    """
    Answer directly from LLM knowledge without tools.
    Used for explanations, code, concepts, prompts etc.
    """
    try:
        llm = get_llm(temperature=0.5)

        if conversation_history:
            user_message = f"""Conversation history:
{conversation_history}

Current question: {task}

Answer thoroughly and accurately. Use markdown formatting."""
        else:
            user_message = f"""{task}

Answer thoroughly and accurately. Use markdown formatting."""

        messages = [
            SystemMessage(content=DIRECT_ANSWER_SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ]

        response = llm.invoke(messages)
        return response.content.strip()

    except Exception as e:
        return f"Error generating response: {str(e)}"


def get_chat_response(task: str, conversation_history: str = "") -> str:
    """Simple conversational response."""
    try:
        llm = get_llm(temperature=0.7)

        if conversation_history:
            user_message = f"""Conversation so far:
{conversation_history}

User says: {task}"""
        else:
            user_message = task

        messages = [
            SystemMessage(content=CHAT_SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ]

        response = llm.invoke(messages)
        return response.content.strip()

    except Exception as e:
        return "Hello! I am NEXUS. How can I help you today?"


def plan_task(task: str, file_context: str = "") -> List[Dict[str, Any]]:
    """Break down a complex task into tool-based subtasks."""
    try:
        llm = get_llm(temperature=0.2)

        user_message = f"Task: {task}"
        if file_context:
            user_message += f"\n\nContext: {file_context}"

        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ]

        response = llm.invoke(messages)
        raw_plan = response.content.strip()
        return parse_plan(raw_plan)

    except Exception as e:
        return [{
            "index": 1,
            "tool": "web_search",
            "description": task,
            "raw": task
        }]


def parse_plan(raw_plan: str) -> List[Dict[str, Any]]:
    lines = raw_plan.strip().split("\n")
    subtasks = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(r'^(\d+)\.\s*\[TOOL:\s*(\w+)\]\s*(.+)$', line, re.IGNORECASE)
        if match:
            subtasks.append({
                "index": int(match.group(1)),
                "tool": match.group(2).lower().strip(),
                "description": match.group(3).strip(),
                "raw": line
            })
        elif re.match(r'^\d+\.', line):
            parts = line.split(".", 1)
            description = parts[1].strip() if len(parts) > 1 else line
            subtasks.append({
                "index": len(subtasks) + 1,
                "tool": "web_search",
                "description": description,
                "raw": line
            })

    if not subtasks:
        subtasks = [{
            "index": 1,
            "tool": "web_search",
            "description": raw_plan[:200],
            "raw": raw_plan[:200]
        }]

    return subtasks


def select_tool_for_task(task: str) -> str:
    task_lower = task.lower()
    if any(w in task_lower for w in ["calculate", "compute", "math", "+", "-", "*", "/"]):
        return "calculator"
    elif any(w in task_lower for w in ["csv", "excel", "dataset", "dataframe"]):
        return "data_analyzer"
    elif any(w in task_lower for w in ["summarize", "summary", "key points"]):
        return "summarizer"
    elif any(w in task_lower for w in ["read file", "pdf", "docx"]):
        return "file_reader"
    elif any(w in task_lower for w in ["run code", "python", "execute"]):
        return "python_repl"
    elif any(w in task_lower for w in ["wikipedia", "wiki", "who is"]):
        return "wikipedia"
    else:
        return "web_search"