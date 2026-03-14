from tools.search_tool import run_search_tool
from tools.calculator_tool import run_calculator_tool
from tools.wikipedia_tool import run_wikipedia_tool
from tools.file_reader_tool import run_file_reader_tool, register_file, get_registered_files
from tools.python_repl_tool import run_python_repl_tool
from tools.data_analyzer_tool import run_data_analyzer_tool
from tools.summarizer_tool import run_summarizer_tool


# Tool registry — maps tool name to function
TOOL_REGISTRY = {
    "web_search": {
        "func": run_search_tool,
        "description": "Search the web for current information, news, facts. Input: search query string.",
        "example": "latest AI agent frameworks 2024"
    },
    "calculator": {
        "func": run_calculator_tool,
        "description": "Perform mathematical calculations. Input: math expression like '25 * 4 + 10'.",
        "example": "sqrt(144) + 25 * 4"
    },
    "wikipedia": {
        "func": run_wikipedia_tool,
        "description": "Search Wikipedia for factual information about any topic. Input: topic name.",
        "example": "Large Language Models"
    },
    "file_reader": {
        "func": run_file_reader_tool,
        "description": "Read uploaded files — PDF, CSV, DOCX, XLSX, JSON, TXT, images. Input: file_id or filename.",
        "example": "dataset.csv"
    },
    "python_repl": {
        "func": run_python_repl_tool,
        "description": "Execute Python code for data analysis, calculations, and processing. Input: Python code.",
        "example": "import pandas as pd\ndf = pd.DataFrame({'a': [1,2,3]})\nprint(df.describe())"
    },
    "data_analyzer": {
        "func": run_data_analyzer_tool,
        "description": "Automatically analyze any dataset — statistics, correlations, missing values, outliers. Input: file_id or filename.",
        "example": "titanic.csv"
    },
    "summarizer": {
        "func": run_summarizer_tool,
        "description": "Summarize long documents or text into concise key points. Input: text or file_id.",
        "example": "research_paper.pdf"
    },
}


def get_tool(tool_name: str):
    """Get a tool function by name."""
    tool = TOOL_REGISTRY.get(tool_name)
    if tool:
        return tool["func"]
    return None


def get_all_tool_descriptions() -> str:
    """Get formatted descriptions of all available tools."""
    lines = ["Available tools:\n"]
    for name, info in TOOL_REGISTRY.items():
        lines.append(f"- {name}: {info['description']}")
    return "\n".join(lines)


def execute_tool(tool_name: str, tool_input: str) -> tuple[str, bool]:
    """
    Execute a tool by name with given input.
    Returns (result, success)
    """
    tool_func = get_tool(tool_name)
    if not tool_func:
        available = list(TOOL_REGISTRY.keys())
        return f"Tool '{tool_name}' not found. Available: {available}", False

    try:
        result = tool_func(tool_input)
        return result, True
    except Exception as e:
        return f"Tool '{tool_name}' failed: {str(e)}", False


__all__ = [
    "TOOL_REGISTRY",
    "get_tool",
    "get_all_tool_descriptions",
    "execute_tool",
    "register_file",
    "get_registered_files",
]