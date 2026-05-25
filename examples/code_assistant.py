"""Code Assistant Agent - Example for code generation and review

Demonstrates:
- Code generation
- Code review and analysis
- Documentation generation
- Multi-file project creation
"""

import asyncio
from typing import Any, Dict, List

from core.agent import Agent
from core.agent_builder import AgentBuilder
from core.models.models import AgentType
from core.reasoning.chain_of_thought import ReasoningType


def create_code_assistant_agent() -> Agent:
    """Create a code assistant agent."""

    code_tools = [
        {
            "name": "generate_code",
            "description": "Generate code based on requirements",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {"type": "string", "description": "Programming language"},
                    "requirements": {"type": "string", "description": "Code requirements"},
                    "framework": {"type": "string", "description": "Framework to use (optional)"}
                },
                "required": ["language", "requirements"]
            }
        },
        {
            "name": "review_code",
            "description": "Review and analyze code for issues",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to review"},
                    "language": {"type": "string", "description": "Programming language"}
                },
                "required": ["code", "language"]
            }
        },
        {
            "name": "explain_code",
            "description": "Explain what code does",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to explain"}
                },
                "required": ["code"]
            }
        },
        {
            "name": "generate_tests",
            "description": "Generate unit tests for code",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to test"},
                    "language": {"type": "string", "description": "Programming language"},
                    "framework": {"type": "string", "description": "Test framework"}
                },
                "required": ["code", "language"]
            }
        },
        {
            "name": "create_project",
            "description": "Create a multi-file project structure",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Project name"},
                    "project_type": {"type": "string", "description": "Type (web, api, cli, etc.)"},
                    "files": {"type": "array", "description": "List of files to create"}
                },
                "required": ["project_name", "project_type", "files"]
            }
        }
    ]

    agent = (
        AgentBuilder("Code Assistant")
        .with_type(AgentType.AUTONOMOUS)
        .with_tools(code_tools)
        .with_reasoning(ReasoningType.CHAIN_OF_THOUGHT)
        .with_system_prompt("""You are a code assistant that helps with:

1. Code generation - Create clean, efficient code
2. Code review - Find bugs, security issues, improvements
3. Code explanation - Explain complex code in simple terms
4. Test generation - Write comprehensive unit tests
5. Project scaffolding - Create project structures

Always explain your code and provide examples.""")
        .build()
    )

    return agent


class CodeAssistantAgent:
    """Code Assistant with integrated tools."""

    def __init__(self):
        self.agent = create_code_assistant_agent()

        async def execute_tool(tool_name: str, params: Dict):
            if tool_name == "generate_code":
                return self._generate_code(
                    params.get("language"),
                    params.get("requirements"),
                    params.get("framework")
                )
            elif tool_name == "review_code":
                return self._review_code(
                    params.get("code"),
                    params.get("language")
                )
            elif tool_name == "explain_code":
                return self._explain_code(params.get("code"))
            elif tool_name == "generate_tests":
                return self._generate_tests(
                    params.get("code"),
                    params.get("language"),
                    params.get("framework")
                )
            elif tool_name == "create_project":
                return self._create_project(
                    params.get("project_name"),
                    params.get("project_type"),
                    params.get("files")
                )
            return {"error": "Tool not found"}

        self.agent._execute_tool = execute_tool

    def _generate_code(self, language: str, requirements: str, framework: str = None) -> Dict:
        """Generate code based on requirements."""
        templates = {
            "python": {
                "web": '''"""Web application for {requirements}"""
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api', methods=['GET', 'POST'])
def handle_request():
    data = request.get_json()
    return jsonify({{"status": "success", "data": data}})

if __name__ == '__main__':
    app.run(debug=True)
''',
                "api": '''"""API for {requirements}"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class RequestModel(BaseModel):
    data: str

@app.post("/process")
async def process_data(req: RequestModel):
    return {{"result": f"Processed: {{req.data}}"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
                "cli": '''"""CLI tool for {requirements}"""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="{requirements}")
    parser.add_argument("input", help="Input data")
    parser.add_argument("-o", "--output", help="Output file")
    args = parser.parse_args()

    # Process input
    result = process(args.input)

    # Output result
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
    else:
        print(result)

def process(data):
    # TODO: Implement processing logic
    return f"Processed: {{data}}"

if __name__ == "__main__":
    main()
'''
            },
            "javascript": {
                "web": '''// Web application for {requirements}
const express = require('express');
const app = express();

app.use(express.json());

app.get('/api', (req, res) => {{
    res.json({{ status: 'success', data: req.body }});
}});

app.listen(3000, () => {{
    console.log('Server running on port 3000');
}});
'''
            }
        }

        code = templates.get(language, {}).get(framework or "cli", f"// {requirements}")
        code = code.format(requirements=requirements)

        return {
            "success": True,
            "language": language,
            "framework": framework,
            "code": code
        }

    def _review_code(self, code: str, language: str) -> Dict:
        """Review code for issues."""
        issues = []

        # Simple static analysis
        if "eval(" in code:
            issues.append({
                "severity": "high",
                "type": "security",
                "message": "Avoid using eval() - it can execute arbitrary code"
            })

        if "TODO" in code or "FIXME" in code:
            issues.append({
                "severity": "low",
                "type": "incomplete",
                "message": "Code contains TODO/FIXME comments"
            })

        if language == "python":
            if "except:" in code:
                issues.append({
                    "severity": "medium",
                    "type": "best_practice",
                    "message": "Bare except clause - catch specific exceptions"
                })

        # Count lines
        lines = code.split('\n')
        line_count = len(lines)

        return {
            "success": True,
            "issues": issues,
            "summary": {
                "total_issues": len(issues),
                "high_severity": sum(1 for i in issues if i["severity"] == "high"),
                "lines_of_code": line_count
            },
            "recommendations": [
                "Add docstrings to functions",
                "Add type hints for better code clarity",
                "Consider adding error handling"
            ] if not issues else []
        }

    def _explain_code(self, code: str) -> Dict:
        """Explain what code does."""
        # Simple explanation logic
        explanations = []

        if "def " in code or "function" in code:
            explanations.append("This code defines one or more functions")

        if "class " in code:
            explanations.append("It includes class definitions (object-oriented)")

        if "import " in code or "require(" in code:
            explanations.append("The code imports external modules")

        if "if " in code:
            explanations.append("Contains conditional logic")

        if "for " in code or "while " in code:
            explanations.append("Contains loops for iteration")

        return {
            "success": True,
            "explanation": "; ".join(explanations) or "This is a simple code snippet",
            "complexity": "high" if len(code.split('\n')) > 50 else "medium" if len(code.split('\n')) > 20 else "low"
        }

    def _generate_tests(self, code: str, language: str, framework: str = None) -> Dict:
        """Generate unit tests."""
        if language == "python":
            tests = '''"""Unit tests for the code"""
import pytest
from your_module import *

def test_basic():
    """Test basic functionality"""
    assert True

def test_edge_cases():
    """Test edge cases"""
    pass

if __name__ == "__main__":
    pytest.main([__file__])
'''
        elif language == "javascript":
            tests = '''// Unit tests
const assert = require('assert');

function testBasic() {
    assert.strictEqual(1, 1);
}

testBasic();
console.log("All tests passed");
'''
        else:
            tests = "# Tests not available for this language"

        return {
            "success": True,
            "language": language,
            "framework": framework or "default",
            "tests": tests
        }

    def _create_project(self, project_name: str, project_type: str, files: List[Dict]) -> Dict:
        """Create project structure."""
        structure = {
            "project_name": project_name,
            "type": project_type,
            "files": [
                {
                    "path": f["path"],
                    "content": f.get("content", "# Auto-generated file")
                }
                for f in files
            ]
        }

        return {
            "success": True,
            "message": f"Created project '{project_name}' with {len(files)} files",
            "structure": structure
        }

    async def start(self):
        await self.agent.start()

    async def stop(self):
        await self.agent.stop()

    async def generate_code(self, language: str, requirements: str, framework: str = None) -> str:
        """Generate code."""
        response = await self.agent.run(
            f"Generate {language} code for: {requirements}",
            {"framework": framework}
        )
        return response.output

    async def review_code(self, code: str, language: str) -> Dict:
        """Review code."""
        response = await self.agent.run(
            f"Review this {language} code:\n{code}"
        )
        return {"review": response.output}


async def run_code_assistant_demo():
    """Demo the code assistant."""
    print("=" * 50)
    print("Code Assistant Demo")
    print("=" * 50)

    agent = CodeAssistantAgent()
    await agent.start()

    # Test code generation
    print("\n1. Generating Python CLI code...")
    result = await agent.generate_code("python", "process data from file", "cli")
    print(f"Result: {result}")

    # Test code review
    print("\n2. Reviewing code...")
    code = """
def process_data(data):
    eval(data)  # Dangerous!
    TODO: add error handling
    return data
"""
    review = await agent.review_code(code, "python")
    print(f"Issues found: {review['review']}")

    await agent.stop()


if __name__ == "__main__":
    asyncio.run(run_code_assistant_demo())