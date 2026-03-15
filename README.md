# ⚡ NEXUS AGENT — Autonomous AI Agent Platform

<div align="center">

![NEXUS AGENT](https://img.shields.io/badge/NEXUS-AGENT-6366f1?style=for-the-badge&logo=lightning&logoColor=white)
![NeuraX 2.0](https://img.shields.io/badge/NeuraX-2.0%20Hackathon-10b981?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-orange?style=for-the-badge)

**An Autonomous AI Agent that decomposes any task, selects the right tools, maintains memory, and streams its thinking in real-time — built with 100% free APIs.**

[🌐 Live Demo](https://nexus-agent-frontend-rho.vercel.app) • [🔧 Backend API](https://nuerax-hackathon.onrender.com) • [📦 GitHub](https://github.com/bonamukkala-bot/nuerax-hackathon)

</div>

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [What is NEXUS AGENT](#-what-is-nexus-agent)
- [Live URLs](#-live-urls)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Code Files Explained](#-code-files-explained)
- [Installation & Setup](#-installation--setup)
- [API Documentation](#-api-documentation)
- [Demo Scenarios](#-demo-scenarios)
- [Deployment](#-deployment)
- [How to Use](#-how-to-use)

---

## 🎯 Problem Statement

**NeuraX 2.0 Hackathon — AI & Machine Learning Track**

> Build an Autonomous AI Agent that:
> - Decomposes complex tasks into sub-tasks
> - Selects appropriate tools (APIs, databases, search engines)
> - Maintains contextual memory across interactions
> - Executes multi-step workflows with minimal human intervention

NEXUS AGENT solves this completely — it is a full-stack autonomous AI agent that accepts ANY file or question, plans a strategy, picks the right tools, executes step by step, and delivers a comprehensive answer while streaming every thought in real-time.

---

## 🧠 What is NEXUS AGENT

NEXUS AGENT is an **Agentic AI Platform** that works like a smart assistant with a brain:

```
You ask: "Analyze survival patterns in this Titanic CSV"
         ↓
Agent PLANS: Break into subtasks
         ↓
Agent EXECUTES: Runs data_analyzer tool → runs EDA pipeline
         ↓
Agent REFLECTS: Checks results, replans if something fails
         ↓
Agent SYNTHESIZES: Combines all results into a clear answer
         ↓
You get: Charts + Statistics + AI Insights + Downloadable Report
```

It works with **any file type** — CSV, PDF, Excel, DOCX, JSON, images, text files.
It works with **any question** — web search, calculations, Wikipedia lookup, code execution.

---

## 🌐 Live URLs

| Service | URL |
|---------|-----|
| 🖥️ Frontend (Vercel) | https://nexus-agent-frontend-rho.vercel.app |
| 🔧 Backend API (Render) | https://nuerax-hackathon.onrender.com |
| 📚 API Docs | https://nuerax-hackathon.onrender.com/docs |
| ❤️ Health Check | https://nuerax-hackathon.onrender.com/health |

> ⚠️ Note: Backend is on Render free tier — first request may take 50 seconds to wake up.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│              React + Vite (Vercel)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │   Chat   │ │  Files   │ │   EDA    │ │ History  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ WebSocket (wss://)
                     │ REST API (https://)
┌────────────────────▼────────────────────────────────────┐
│                  FASTAPI BACKEND (Render)                │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              LANGGRAPH AGENT LOOP                │   │
│  │                                                  │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐  │   │
│  │  │ PLANNER  │───▶│EXECUTOR  │───▶│REFLECTOR │  │   │
│  │  │          │    │          │    │          │  │   │
│  │  │Decompose │    │Run Tools │    │Check &   │  │   │
│  │  │Task into │    │One by    │    │Replan if │  │   │
│  │  │Subtasks  │    │One       │    │Failed    │  │   │
│  │  └──────────┘    └──────────┘    └────┬─────┘  │   │
│  │                                        │        │   │
│  │                  ┌─────────────────────▼──────┐ │   │
│  │                  │      SYNTHESIZER           │ │   │
│  │                  │  Combine all results into  │ │   │
│  │                  │  one final answer          │ │   │
│  │                  └────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │                   7 TOOLS                       │    │
│  │  web_search │ wikipedia │ calculator            │    │
│  │  file_reader │ python_repl │ data_analyzer      │    │
│  │  summarizer                                     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              3-LAYER MEMORY                     │    │
│  │  Short-term (RAM) │ Long-term (Search)          │    │
│  │  Episodic (SQLite)                              │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                     │
         ┌───────────▼──────────┐
         │   GROQ LLaMA 3.3 70B │
         │   (Free API)         │
         └──────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.11+ | Core language |
| **FastAPI** | 0.115 | REST API + WebSocket server |
| **LangGraph** | Latest | Stateful agent loop |
| **LangChain** | Latest | Tool orchestration |
| **Groq API** | LLaMA 3.3 70B | LLM brain (FREE) |
| **DuckDuckGo Search** | Latest | Web search (FREE, no key) |
| **PyMuPDF** | Latest | PDF text extraction |
| **pandas** | 2.x | Data analysis |
| **matplotlib** | 3.x | Chart generation |
| **seaborn** | Latest | Statistical visualization |
| **python-docx** | Latest | Word document reading |
| **Pillow** | Latest | Image processing |
| **SQLite** | Built-in | Episodic memory storage |
| **wikipedia** | Latest | Wikipedia search (FREE) |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **React** | 18 | UI framework |
| **Vite** | 8 | Build tool |
| **Firebase** | Latest | Authentication |
| **WebSocket** | Native | Real-time streaming |

### Infrastructure
| Service | Purpose | Cost |
|---------|---------|------|
| **Render** | Backend hosting | FREE |
| **Vercel** | Frontend hosting | FREE |
| **Firebase** | Authentication | FREE |
| **Groq** | LLM API | FREE |

---

## ✨ Features

### 🤖 Autonomous Agent
- **Task Decomposition** — Breaks any complex task into 2-4 ordered subtasks
- **Tool Selection** — Automatically picks the right tool for each subtask
- **Self-healing** — If a tool fails, agent replans with a different approach
- **Real-time Streaming** — Every thought streams live to the UI

### 📁 Universal File Support
- **PDF** — Page-by-page text extraction using PyMuPDF
- **CSV/Excel** — Full data analysis with pandas
- **DOCX** — Word document reading with python-docx
- **JSON** — Structured data parsing
- **Images** — Size and format info with Pillow
- **TXT/MD** — Direct text reading
- **URLs** — Web scraping with BeautifulSoup

### 📊 Agentic EDA Pipeline
- **Coder Agent** — LLM writes Python EDA code automatically
- **Analyst Agent** — Explains findings in plain English
- **Distribution Charts** — Histogram + Boxplot for every numeric column
- **Correlation Heatmap** — Relationships between all numeric features
- **Missing Values Chart** — Visual missing data analysis
- **Categorical Charts** — Value counts for text columns
- **Pairplot** — Feature relationships visualization
- **Downloadable Report** — Full EDA report as text file

### 🧠 3-Layer Memory System
- **Short-term** — Conversation history within session
- **Long-term** — Uploaded file content searchable by keyword
- **Episodic** — All past runs saved in SQLite database

### 🔐 Firebase Authentication
- **Google Sign-in** — One-click authentication
- **Email/Password** — Traditional login and registration
- **Session Persistence** — Stay logged in across browser refreshes

### 🔧 7 Powerful Tools
1. **Web Search** — DuckDuckGo real-time search
2. **Wikipedia** — Factual knowledge lookup
3. **Calculator** — Safe math expression evaluator
4. **File Reader** — Universal file content extractor
5. **Python REPL** — Safe sandboxed code execution
6. **Data Analyzer** — Auto EDA engine
7. **Summarizer** — Extractive document summarization

---

## 📁 Project Structure

```
nexus-agent/
│
├── backend/                          # Python FastAPI backend
│   ├── main.py                       # Server entry point + all API endpoints
│   ├── requirements.txt              # Python dependencies
│   ├── .env                          # Environment variables (API keys)
│   │
│   ├── agent/                        # LangGraph agent system
│   │   ├── __init__.py               # Package exports
│   │   ├── graph.py                  # Main agent loop (Planner→Executor→Reflector→Synthesizer)
│   │   ├── planner.py                # Task decomposition into subtasks
│   │   ├── synthesizer.py            # Final answer generation
│   │   └── memory_manager.py         # Unified memory interface
│   │
│   ├── tools/                        # All agent tools
│   │   ├── __init__.py               # Tool registry + execute_tool()
│   │   ├── search_tool.py            # DuckDuckGo web search
│   │   ├── calculator_tool.py        # Safe math evaluator
│   │   ├── wikipedia_tool.py         # Wikipedia search
│   │   ├── file_reader_tool.py       # Universal file reader
│   │   ├── python_repl_tool.py       # Safe Python code executor
│   │   ├── data_analyzer_tool.py     # Auto EDA + chart generation
│   │   └── summarizer_tool.py        # Text summarization
│   │
│   ├── memory/                       # 3-layer memory system
│   │   ├── __init__.py               # Package exports
│   │   ├── short_term.py             # Session conversation memory (RAM)
│   │   ├── long_term.py              # Document search memory
│   │   └── episodic.py               # SQLite run history
│   │
│   ├── ingestion/                    # File upload pipeline
│   │   ├── __init__.py               # Package exports
│   │   └── universal_loader.py       # Save → Read → Chunk → Store pipeline
│   │
│   └── uploads/                      # Uploaded files stored here
│
└── frontend/                         # React frontend
    ├── index.html                    # HTML entry point
    ├── vite.config.js                # Vite configuration
    ├── package.json                  # Node dependencies
    ├── .npmrc                        # NPM config (legacy-peer-deps)
    │
    └── src/
        ├── main.jsx                  # React app entry point
        ├── App.jsx                   # Main application UI (all tabs)
        ├── Auth.jsx                  # Firebase login/register UI
        ├── firebase.js               # Firebase initialization
        └── index.css                 # Global styles
```

---

## 📖 Code Files Explained

---

### 🔴 BACKEND

---

#### `backend/main.py` — API Server

The entry point of the entire backend. Creates the FastAPI app, sets up CORS, and defines all endpoints.

```python
# Key endpoints:
GET  /           → Root info
GET  /health     → Health check
POST /upload     → Upload any file
POST /query      → REST chat endpoint
WS   /ws/{id}   → WebSocket real-time streaming
GET  /history    → All agent run history
POST /eda/{id}   → Run full EDA on uploaded file
GET  /files      → List uploaded files

# CORS is set to allow all origins (*) so frontend can connect
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# WebSocket handles real-time streaming:
# 1. Receive task from browser
# 2. Call run_agent()
# 3. Stream every event back (thoughts, steps, final answer)
```

**Why FastAPI:** Async support, automatic API docs, WebSocket support, fast performance.

---

#### `backend/agent/graph.py` — The Brain (Most Important File)

Defines the LangGraph stateful agent loop. This is the core of the entire project.

```python
# AgentState — the data passed between all nodes
class AgentState(TypedDict):
    session_id: str
    task: str
    subtasks: List[Dict]        # planned subtasks
    current_step_index: int     # which step we're on
    completed_steps: List[Dict] # finished steps with results
    final_answer: str
    confidence: float
    thoughts: List[str]         # streaming thought log
    status: str                 # planning/executing/synthesizing/completed

# 4 NODES in the graph:

def planner_node(state):
    # Gets memory context
    # Calls decompose_task() to break task into subtasks
    # Each subtask has: step, subtask description, tool, tool_input

def executor_node(state):
    # Takes current subtask
    # Calls execute_tool(tool_name, tool_input)
    # Records result + success/failure + duration
    # Saves tool call to episodic memory

def reflector_node(state):
    # If last step FAILED → calls replan_after_failure()
    # If all steps DONE → moves to synthesizer
    # Otherwise → loops back to executor

def synthesizer_node(state):
    # Calls synthesize_results() with all completed steps
    # Gets final answer + confidence score
    # Saves complete run to episodic memory

# Graph connections:
# planner → executor → reflector → (executor loop OR synthesizer) → END

# Main entry point:
async def run_agent(task, session_id, context, on_thought):
    # Builds and runs the graph
    # Returns final answer with all metadata
```

**Why LangGraph:** Unlike simple LangChain chains, LangGraph supports loops, conditional edges, and stateful execution — perfect for agents that need to retry and replan.

---

#### `backend/agent/planner.py` — Task Decomposer

Breaks any task into an ordered list of subtasks with tool assignments.

```python
# Detects 3 types of tasks:

def is_conversational(task):
    # "hello", "hi", "thanks", "what can you do"
    # → Returns True for simple chat messages

def is_file_task(task):
    # "analyze", "summarize", "in the csv", "uploaded file"
    # → Returns True when task involves uploaded files

def decompose_task(task, context):
    # If conversational → 1 step, use wikipedia
    # If file task → 2 steps: data_analyzer + summarizer
    # Otherwise → Ask LLM to plan 2-4 steps
    
    # LLM gets list of all available tools + their descriptions
    # Returns JSON array of subtasks like:
    # [
    #   {"step": 1, "subtask": "...", "tool": "web_search", 
    #    "tool_input": "...", "reason": "..."},
    #   ...
    # ]

def replan_after_failure(original_task, failed_step, reason, completed):
    # Called when a tool fails
    # Asks LLM to suggest alternative steps
    # Uses different tools than the one that failed
```

---

#### `backend/agent/synthesizer.py` — Answer Generator

Takes all tool results and generates one clean, readable final answer.

```python
def is_conversational(task):
    # Detects simple questions
    # Uses shorter, friendlier prompt for these

def synthesize_results(original_task, completed_steps, context):
    # Builds summary of all steps:
    # "Step 1 [SUCCESS] - searched web → found 5 results"
    # "Step 2 [SUCCESS] - analyzed data → found 3 patterns"
    
    # Two system prompts:
    # CONVERSATIONAL: 2-4 sentences, friendly, no headers
    # RESEARCH: structured, bullet points, bold terms
    
    # Strips "CONFIDENCE: XX" from response
    # Returns: answer, confidence score, tools_used list

def generate_report(task, answer, steps, confidence):
    # Creates formatted text report for download
    # Used by EDA pipeline
```

---

#### `backend/agent/memory_manager.py` — Memory Controller

Single interface to manage all 3 memory layers per session.

```python
class AgentMemoryManager:
    def __init__(self, session_id):
        self.short_term = get_session_memory(session_id)
        self.long_term = get_long_term_memory()
    
    def add_user_message(message)     # Save user input
    def add_agent_message(message)    # Save agent response
    def add_tool_result(tool, result) # Save tool output
    
    def get_conversation_context()    # Last 10 messages as string
    def search_relevant_knowledge(q)  # Search uploaded files
    
    def get_full_context(query):
        # Combines BOTH conversation + file knowledge
        # Used to enrich every agent prompt
    
    def set_uploaded_file(file_id, filename)  # Remember uploads
    def get_uploaded_files()                  # List session files
    def get_memory_summary()                  # Stats about memory
```

---

### 🟡 TOOLS

---

#### `backend/tools/search_tool.py` — Web Search

```python
def search_web(query, max_results=5):
    # Uses DuckDuckGo DDGS library
    # Returns formatted results:
    # "1. Title\n   Description\n   Source: URL\n"
    # No API key needed — completely free

def search_news(query, max_results=5):
    # Searches for recent news specifically
    # Returns news with source names

def run_search_tool(input):
    # Main entry point called by agent
    # Calls search_web(input)
```

---

#### `backend/tools/calculator_tool.py` — Math Engine

```python
def calculate(expression):
    # Cleans expression (^ → **, × → *, ÷ → /)
    # Available functions:
    #   sqrt, sin, cos, tan, log, log2, log10, exp
    #   floor, ceil, factorial, gcd, abs, round
    #   Constants: pi, e, inf
    
    # Safety: uses restricted globals — no dangerous builtins
    # Returns: "Result: 25 * 4 = 100"

def run_calculator_tool(input):
    # Strips natural language: "what is", "calculate", "compute"
    # Then calls calculate()
```

---

#### `backend/tools/wikipedia_tool.py` — Knowledge Lookup

```python
def search_wikipedia(query, sentences=5):
    # Sets language to English
    # Searches for top 3 matches
    # Gets page summary (5 sentences by default)
    
    # Handles errors:
    # DisambiguationError → tries first option
    # PageError → tries second search result
    
    # Returns: "Wikipedia: {title}\n\n{summary}\n\nSource: {url}"

def run_wikipedia_tool(input):
    # Cleans input (removes "wikipedia", "search for", "look up")
    # Calls search_wikipedia()
```

---

#### `backend/tools/file_reader_tool.py` — Universal File Reader

```python
# Global file registry
_uploaded_files = {}  # {file_id: {path, name, extension}}

def register_file(file_id, file_path, original_name):
    # Called after upload to register file for agent access

def read_file(file_path, original_name):
    # Auto-detects extension and routes to correct reader:
    # .pdf  → read_pdf()
    # .docx → read_docx()
    # .csv  → read_csv()
    # .xlsx → read_excel()
    # .json → read_json()
    # .txt  → read_text()
    # .png/.jpg → read_image()

def read_pdf(file_path):
    # PyMuPDF opens PDF
    # Extracts text page by page
    # Returns "--- Page 1 ---\ntext\n--- Page 2 ---\ntext"
    # Truncates at 5000 chars with note

def read_csv(file_path):
    # pandas reads CSV
    # Returns: rows, columns, first 10 rows, dtypes, missing values

def read_image(file_path):
    # Pillow opens image
    # Returns: size, format info
    # (OCR disabled in cloud deployment)

def read_url(url):
    # requests + BeautifulSoup scrapes webpage
    # Removes scripts, styles, nav, footer
    # Returns clean text content

def run_file_reader_tool(input):
    # Checks if URL → calls read_url()
    # Checks registered files by file_id
    # Checks by filename
    # Falls back to direct path check
```

---

#### `backend/tools/python_repl_tool.py` — Safe Code Executor

```python
def is_safe_code(code):
    # Blocks dangerous patterns:
    # import os, import sys, import subprocess
    # open(), exec(), eval(), import socket
    # Returns (is_safe, reason)

def execute_python(code):
    # Captures stdout with StringIO
    # Available safe modules:
    #   math, json, re, statistics, datetime
    #   pandas (as pd), numpy (as np)
    
    # Uses restricted builtins:
    #   print, len, range, enumerate, zip, map
    #   sorted, list, dict, set, str, int, float
    #   round, abs, max, min, sum, type, isinstance
    
    # Returns stdout output or error traceback

def run_python_repl_tool(input):
    # Strips markdown code blocks (```python ... ```)
    # Calls execute_python()
```

---

#### `backend/tools/data_analyzer_tool.py` — EDA Engine

This is the most feature-rich tool, implementing the full Agentic EDA Pipeline.

```python
# Two AI agents:

CODER_AGENT_PROMPT = """
You are a Python Data Scientist.
Write Python EDA code for the given dataset.
The dataframe is already loaded as 'df'.
Use only pandas and numpy.
Print all outputs.
"""

ANALYST_AGENT_PROMPT = """
You are a Data Analyst.
Explain EDA statistics in plain English.
Format response with sections:
## Dataset Overview
## Key Findings  
## Data Quality Issues
## ML Preprocessing Suggestions
## Top 3 Recommendations
"""

def run_coder_agent(df):
    # Sends dataset info to LLM
    # LLM generates Python EDA code
    # Executes code safely
    # Returns printed statistics output

def run_analyst_agent(stats_output, df_info):
    # Sends statistics to LLM
    # LLM explains in plain English
    # Returns formatted insights

# Chart generation functions:
def generate_distribution_charts(df):
    # For each numeric column (up to 6):
    # Left: Histogram (purple bars)
    # Right: Boxplot (shows outliers)
    # Dark theme (#0f0f0f background)
    # Returns list of base64 PNG images

def generate_correlation_heatmap(df):
    # seaborn heatmap with coolwarm colormap
    # Mask upper triangle (avoid duplicate)
    # Annotates cells with correlation values

def generate_missing_values_chart(df):
    # Horizontal bar chart
    # Red bars for >30% missing, yellow for less
    # Shows percentage labels on each bar

def generate_categorical_charts(df):
    # For each categorical column (up to 4):
    # Horizontal bar chart of top 10 values
    # Colorful (Set3 colormap)

def generate_pairplot(df):
    # Scatter plots between all numeric pairs
    # Histogram on diagonal
    # Samples 1000 rows for speed

def run_full_eda(file_path):
    # Complete pipeline:
    # 1. Load file (CSV/Excel/JSON)
    # 2. Generate all charts
    # 3. Run Coder Agent → get statistics
    # 4. Run Analyst Agent → get insights
    # 5. Generate downloadable report
    # Returns: {charts, stats_output, ai_insights, report, summary}
```

---

#### `backend/tools/summarizer_tool.py` — Text Summarizer

```python
def simple_extractive_summary(text, num_sentences=5):
    # No LLM needed — pure algorithm
    # Scores sentences by:
    #   Position (first/last sentences are important)
    #   Keyword frequency (common words = important)
    # Picks top N sentences
    # Re-sorts by original position

def summarize_text(text, max_length=500, style='concise'):
    # style='concise'  → 5 sentences
    # style='detailed' → 10 sentences  
    # style='bullets'  → bullet point list

def summarize_document(text, title):
    # Creates structured summary:
    # Title + word count + char count
    # Main summary (6 sentences)
    # Key sentences (top 5)

def run_summarizer_tool(input):
    # Checks if input is file_id → reads file first
    # Checks if input is filename → reads file first
    # Otherwise summarizes input text directly
```

---

#### `backend/tools/__init__.py` — Tool Registry

```python
# Central registry of all tools
TOOL_REGISTRY = {
    "web_search": {
        "func": run_search_tool,
        "description": "Search the web...",
        "example": "latest AI agent frameworks"
    },
    "calculator": {...},
    "wikipedia": {...},
    "file_reader": {...},
    "python_repl": {...},
    "data_analyzer": {...},
    "summarizer": {...}
}

def execute_tool(tool_name, tool_input):
    # Looks up tool in registry
    # Calls tool function
    # Returns (result, success)
    # Handles exceptions gracefully

def get_all_tool_descriptions():
    # Returns formatted string of all tools
    # Used in LLM prompts so agent knows what tools exist
```

---

### 🟢 MEMORY

---

#### `backend/memory/short_term.py` — Session Memory

```python
class ShortTermMemory:
    def __init__(self, max_messages=20):
        self.messages = []         # conversation history
        self.session_data = {}     # key-value store for session
    
    def add_message(role, content):
        # Adds to messages list
        # Keeps only last 20 messages (sliding window)
    
    def get_context_string():
        # Returns last 10 messages as:
        # "USER: hello\nASSISTANT: hi there\n..."
    
    def set_session_data(key, value):  # Store anything in session
    def get_session_data(key):         # Retrieve session data

# Global session store:
_sessions = {}  # {session_id: ShortTermMemory}

def get_session_memory(session_id):
    # Creates new memory if session doesn't exist
    # Returns existing memory if it does
```

---

#### `backend/memory/long_term.py` — Document Memory

```python
class LongTermMemory:
    def __init__(self):
        self.documents = []  # List of {content, metadata} dicts
    
    def add_documents(texts, metadatas):
        # Stores text chunks with metadata
        # Called after file upload
    
    def search(query, k=5):
        # Keyword-based search (no ML needed, lightweight):
        # 1. Splits query into words
        # 2. Counts how many query words appear in each document
        # 3. Returns top k highest scoring documents
    
    def search_relevant_context(query, k=3):
        # Returns top k results as joined string
        # Used to inject context into agent prompts
    
    def add_fact(fact, source):
        # Convenience method to add single fact
```

---

#### `backend/memory/episodic.py` — Run History

```python
# SQLite database with 2 tables:

# Table 1: agent_runs
# id | session_id | task | subtasks | tools_used | 
# final_answer | confidence | duration | timestamp | status

# Table 2: tool_calls  
# id | session_id | run_id | tool_name | tool_input |
# tool_output | success | timestamp

def init_db():
    # Creates tables if they don't exist
    # Called on server startup

def save_agent_run(session_id, task, subtasks, tools_used, 
                   final_answer, confidence, duration, status):
    # Saves complete agent run to database
    # Returns run_id

def save_tool_call(session_id, run_id, tool_name, 
                   tool_input, tool_output, success):
    # Saves each individual tool call
    # Truncates long inputs/outputs for storage

def get_recent_runs(session_id, limit=10):
    # Gets recent runs for a specific session
    # Parses JSON fields back to Python objects

def get_all_runs(limit=50):
    # Gets all runs across all sessions
    # Used by /history endpoint and History tab
```

---

### 🔵 INGESTION

---

#### `backend/ingestion/universal_loader.py` — File Pipeline

```python
UPLOAD_DIR = "../uploads"  # Where files are saved on disk

def save_uploaded_file(file_bytes, original_filename):
    # Generates unique 8-char file_id (UUID)
    # Saves file as {file_id}{extension}
    # Calls register_file() so agent can access it
    # Returns (file_id, file_path)

def load_and_chunk(file_path, original_filename):
    # Reads file content using file_reader_tool
    # CSV/Excel → single chunk (structured data, don't split)
    # Text files → RecursiveCharacterTextSplitter:
    #   chunk_size=1000, chunk_overlap=100
    #   separators=["\n\n", "\n", ". ", " ", ""]
    # Returns list of {content, metadata} chunks

def process_uploaded_file(file_bytes, original_filename):
    # Complete pipeline:
    # Step 1: save_uploaded_file()
    # Step 2: load_and_chunk()
    # Step 3: Store in long_term memory (small files only, ≤20 chunks)
    # Step 4: Return summary with file_id, chunks count, preview
    
    # Why only small files for memory:
    # Large files would slow down upload significantly
```

---

### 🟣 FRONTEND

---

#### `frontend/src/App.jsx` — Main UI (450+ lines)

```javascript
// State variables:
const [sessionId]      // Persistent session ID (localStorage)
const [messages]       // Chat message history
const [input]          // Current input text
const [isLoading]      // Agent working indicator
const [thoughts]       // Live thought streaming
const [uploadedFiles]  // Files uploaded this session
const [uploadedFile]   // Currently active file
const [activeTab]      // chat/files/eda/history
const [edaData]        // EDA results from backend
const [history]        // Agent run history

// WebSocket connection:
const connectWebSocket = () => {
    ws = new WebSocket('wss://nuerax-hackathon.onrender.com/ws/{sessionId}')
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        // Handle different message types:
        if (data.type === 'thought')     → add to thoughts list
        if (data.type === 'plan')        → add planning thought
        if (data.type === 'tool_start')  → add tool thought
        if (data.type === 'tool_result') → add result thought
        if (data.type === 'answer')      → show final response
        if (data.type === 'error')       → show error message
    }
    
    ws.onclose = () => setTimeout(connectWebSocket, 2000)  // Auto-reconnect
}

// File upload:
const handleFileUpload = async (file) => {
    // POST to /upload with FormData
    // Shows ⏳ uploading message
    // Shows ✅ success with chunk count
    // Updates uploadedFile state for context
}

// EDA trigger:
const runEDA = async (fileInfo) => {
    // POST to /eda/{file_id}
    // Sets edaLoading = true
    // Switches to EDA tab
    // Sets edaData when complete
}

// Message rendering:
const renderMessage = (content) => {
    // Parses markdown-like formatting:
    // ## heading  → purple bold text
    // # heading   → indigo bold text
    // - item      → bullet point with • symbol
    // **bold**    → <strong> tags
    // blank line  → <br>
}

// 4 Tabs:
// 💬 Chat    → messages + input area + file upload button
// 📁 Files   → list of uploaded files + Analyze/EDA buttons
// 📊 EDA     → full EDA dashboard with charts + insights
// 📜 History → all past agent runs from database
```

---

#### `frontend/src/Auth.jsx` — Login Page

```javascript
// Two tabs: Login and Register

// Google Sign-in:
const handleGoogle = async () => {
    const provider = new GoogleAuthProvider()
    await signInWithPopup(auth, provider)
    // Firebase handles everything automatically
}

// Email/Password Login:
const handleLogin = async () => {
    await signInWithEmailAndPassword(auth, email, password)
}

// Email/Password Register:
const handleRegister = async () => {
    await createUserWithEmailAndPassword(auth, email, password)
}

// Shows error messages for:
// auth/user-not-found, auth/wrong-password
// auth/email-already-in-use, auth/weak-password
// auth/unauthorized-domain
```

---

#### `frontend/src/firebase.js` — Firebase Config

```javascript
const firebaseConfig = {
    apiKey: "...",
    authDomain: "nexus-agent-6630e.firebaseapp.com",
    projectId: "nexus-agent",
    storageBucket: "...",
    messagingSenderId: "...",
    appId: "..."
}

const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
// auth is imported by Auth.jsx and App.jsx
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone Repository
```bash
git clone https://github.com/bonamukkala-bot/nuerax-hackathon.git
cd nuerax-hackathon
```

### 2. Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add your GROQ_API_KEY from console.groq.com
```

### 3. Get Free API Keys
| Key | Where to get | Cost |
|-----|-------------|------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | FREE |

### 4. Start Backend
```bash
cd backend
python main.py
# Server starts at http://localhost:8000
```

### 5. Frontend Setup
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
# App starts at http://localhost:5173
```

### 6. Environment Variables

Create `backend/.env`:
```env
GROQ_API_KEY=gsk_your_groq_key_here
GEMINI_API_KEY=optional_backup_key
```

---

## 📡 API Documentation

### REST Endpoints

#### `GET /health`
```json
Response: {"status": "ok", "timestamp": 1234567890}
```

#### `POST /upload`
```
Request: multipart/form-data with file
Response: {
    "success": true,
    "file_id": "abc12345",
    "filename": "data.csv",
    "chunks": 12,
    "preview": "first 300 chars..."
}
```

#### `POST /query`
```json
Request: {"task": "analyze this dataset", "session_id": "abc123"}
Response: {
    "success": true,
    "answer": "final answer text",
    "confidence": 85,
    "tools_used": ["data_analyzer", "summarizer"],
    "steps": [...]
}
```

#### `POST /eda/{file_id}`
```json
Response: {
    "success": true,
    "summary": {"rows": 891, "columns": 12, ...},
    "charts": [{"type": "distribution", "image": "base64..."}],
    "stats_output": "coder agent output...",
    "ai_insights": "analyst agent insights...",
    "report": "full text report..."
}
```

#### `GET /history`
```json
Response: {"runs": [{
    "task": "...",
    "final_answer": "...",
    "confidence": 85,
    "tools_used": ["web_search"],
    "timestamp": 1234567890
}]}
```

### WebSocket Protocol

**Connect:** `ws://localhost:8000/ws/{session_id}`

**Send:**
```json
{
    "task": "What is machine learning?",
    "file_id": "abc123",
    "filename": "data.csv"
}
```

**Receive (streaming):**
```json
{"type": "thought", "content": "Planning task..."}
{"type": "plan", "content": "Created 2 subtasks..."}
{"type": "tool_start", "content": "Using web_search..."}
{"type": "tool_result", "content": "Found 5 results..."}
{"type": "answer", "content": "Final answer text", "confidence": 85, "tools_used": [...]}
{"type": "error", "content": "Error message"}
```

---

## 🎬 Demo Scenarios

### Demo 1 — Simple Question
```
Input: "What is machine learning?"
→ Agent uses: wikipedia
→ Answer: Clear explanation in 3-4 sentences
```

### Demo 2 — Web Search
```
Input: "What are the latest AI agent frameworks in 2025?"
→ Agent uses: web_search
→ Answer: Current information from the web
```

### Demo 3 — Math Calculation
```
Input: "Calculate compound interest: 50000 at 10% for 5 years"
→ Agent uses: calculator + python_repl
→ Answer: Step-by-step calculation result
```

### Demo 4 — File Analysis (CSV)
```
Upload: titanic.csv
Input: "Analyze survival patterns in this dataset"
→ Agent uses: data_analyzer + summarizer
→ Answer: Statistics, patterns, insights
```

### Demo 5 — EDA Pipeline
```
Upload: any CSV file
Click: 📊 EDA button in Files tab
→ Coder Agent writes EDA code
→ 8+ charts generated
→ Analyst Agent explains findings
→ Download full report
```

### Demo 6 — PDF Analysis
```
Upload: research_paper.pdf
Input: "Summarize this paper and find related work online"
→ Agent uses: file_reader + summarizer + web_search
→ Answer: Summary + related papers from web
```

### Demo 7 — Code Execution
```
Input: "Write Python code for bubble sort and test it"
→ Agent uses: python_repl
→ Answer: Code + execution output
```

---

## 🚢 Deployment

### Backend — Render

1. Go to [render.com](https://render.com) → New Web Service
2. Connect GitHub repo: `nuerax-hackathon`
3. Settings:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Environment Variables:
   - `GROQ_API_KEY` = your key
   - `PYTHON_VERSION` = 3.11.0
5. Click **Deploy**

### Frontend — Vercel

```bash
cd frontend
npx vercel --prod
# Follow prompts
# Get production URL
```

### Firebase Auth Setup

1. Go to [console.firebase.google.com](https://console.firebase.google.com)
2. Create project → Enable Authentication
3. Enable: Google + Email/Password providers
4. Add Vercel domain to Authorized Domains
5. Update `frontend/src/firebase.js` with your config

---

## 🔑 How to Use

### 1. Login
- Go to the app URL
- Sign in with Google or Email/Password

### 2. Ask a Question
- Type any question in the chat box
- Press Enter or click Send
- Watch the agent think in real-time

### 3. Upload a File
- Click the 📎 button in chat
- Select any CSV, PDF, DOCX, JSON, or image
- Ask questions about it after upload

### 4. Run EDA Analysis
- Upload a CSV or Excel file
- Go to Files tab
- Click the 📊 EDA button
- Get full automated analysis with charts

### 5. View History
- Click History tab
- See all past agent runs
- Review tools used and confidence scores

---

## 🏆 Hackathon Evaluation Mapping

| Criteria | How NEXUS AGENT Addresses It |
|---------|------------------------------|
| **Problem Understanding** | Directly solves AI agent task decomposition problem |
| **Innovation** | Agentic EDA pipeline with dual AI agents is unique |
| **Feasibility** | Fully working, deployed, 100% free APIs |
| **Technical Approach** | LangGraph + LangChain + FastAPI + React |
| **Potential Impact** | Works with any dataset/file, real-world applicable |
| **Working Prototype** | Live at nexus-agent-frontend-rho.vercel.app |
| **Technical Depth** | 7 tools, 3-layer memory, stateful graph, WebSocket |
| **System Design** | Modular architecture, clean separation of concerns |
| **Scalability** | Stateless backend, session-based memory |
| **User Experience** | Real-time streaming, dark UI, tab navigation |

---

## 💡 One-Line Pitch

> **"NEXUS AGENT is a full-stack autonomous AI agent that accepts any file or question, decomposes it into subtasks, selects the right tools, maintains 3-layer memory, and streams its thinking in real-time — all powered by 100% free APIs and deployed on cloud."**

---

## 👨‍💻 Built For

**NeuraX 2.0 — National Level 24-Hour Hackathon**
CMR Technical Campus
