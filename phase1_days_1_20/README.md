# Phase 1: AI Foundations (Days 1-20)

Goal: Move from basic JS to AI-ready Python and understand how LLMs actually "think."

## Overview

This phase covers:
- Python for JavaScript Developers
- AsyncIO and Advanced Python
- OpenAI API & Structured Outputs
- Prompt Engineering
- Vector Databases & RAG
- FastAPI & WebSockets

## Days

| Day | Topic | Description |
|-----|-------|-------------|
| 1 | Python Basics | Python syntax, lists, dicts, list comprehensions |
| 2 | AsyncIO | Asynchronous programming, heartbeat monitor |
| 3 | OpenAI API | API integration, Pydantic, structured outputs |
| 4 | Prompt Engineering | System prompts, few-shot prompting, gatekeeper |
| 5 | Vector Databases | Embeddings, cosine similarity, memory storage |
| 6 | RAG Pipelines | Retrieval Augmented Generation |
| 7 | Semantic Router | Intent classification, traffic controller |
| 8 | Token Management | Tiktoken, cost optimization |
| 9 | JSON Mode & Function Calling | Tool definitions, Swiss Army Agent |
| 10 | Persistent Memory Store | Postgres + pgvector |
| 11 | Local LLMs (Ollama) | Running models locally |
| 12 | Advanced RAG | Re-ranking, context compression |
| 13 | Python Decorators | Design patterns, secure execution |
| 14 | FastAPI | Web framework for AI agents |
| 15 | WebSockets | Real-time agent communication |
| 16 | Evaluation & Testing | RAGAS, LLM-as-a-Judge |
| 17 | Multi-Modal | Vision, image analysis |
| 18 | State Management | Finite State Machines |
| 19 | Security Basics | Environment variables, vault |
| 20 | Phase 1 Review | Mini-AgentOS CLI |

## Mini-Project (Day 20)

Build a "Mini-AgentOS" CLI with:
1. User creates an "Agent" with a "Personality" (Prompt)
2. Agent can "Remember" things (Vector DB)
3. Agent can "Call a Tool" (JSON Mode)
4. All actions are logged (Decorators)

## Running the Code

```bash
# Install Python dependencies for Phase 1
pip install -r requirements.txt

# Run individual day examples
python day01_basics/agent_identity_parser.py
python day03_openai/schema_enforcer.py
```