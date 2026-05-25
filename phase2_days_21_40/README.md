# Phase 2: Agent Frameworks & Multi-Agent Systems (Days 21-40)

## Overview

This phase covers agent frameworks and multi-agent orchestration:

| Day | Topic | Description |
|-----|-------|-------------|
| 21 | LangChain Basics | Core concepts, prompt templates, chains |
| 22 | LCEL & Chains | LangChain Expression Language, composable chains |
| 23 | CrewAI | Multi-agent teams with role-based agents |
| 24 | AutoGen | Advanced multi-agent conversations |
| 25 | Tool Use Patterns | Integrating tools with agents |
| 26 | Agent Patterns | ReAct, Reflexion, Plan-Execute patterns |
| 27-40 | Advanced Frameworks | More frameworks and patterns |

## Running the Code

```bash
# Install dependencies
pip install langchain openai

# Run individual examples
python day21_langchain_basics.py
python day23_crewai.py
python day24_autogen.py
```

## Key Concepts

### LangChain
- **Chains**: Composable sequences of operations
- **LCEL**: Declarative chain composition
- **Agents**: Chains that can use tools

### Multi-Agent Systems
- **CrewAI**: Role-based agent teams
- **AutoGen**: Conversational multi-agent
- **Orchestration**: Coordinating multiple agents

### Agent Patterns
- **ReAct**: Reasoning + Acting
- **Reflexion**: Self-reflection on failures
- **Plan-Execute**: Plan first, then execute