"""Example usage of AgentOS."""

import asyncio
from agentos.core import (
    get_runtime,
    get_memory_manager,
    get_tool_registry,
    get_governance_engine
)
from agentos.core.models import AgentType


async def main():
    print("=" * 50)
    print("AgentOS Example")
    print("=" * 50)

    # Get services
    runtime = get_runtime()
    memory = get_memory_manager()
    tools = get_tool_registry()
    governance = get_governance_engine()

    # 1. Create an agent
    print("\n1. Creating agent...")
    agent = await runtime.create_agent(
        name="Assistant",
        agent_type=AgentType.CHAT,
        description="A helpful assistant"
    )
    print(f"   Created: {agent.name} ({agent.id})")

    # 2. Run a task
    print("\n2. Running task...")
    task = await runtime.create_task(
        agent_id=agent.id,
        input_data={"message": "Hello, how are you?"}
    )
    result = await runtime.execute_task(task.id)
    print(f"   Result: {result.data}")

    # 3. Store memory
    print("\n3. Storing memory...")
    memory_id = await memory.add_short_term(
        agent_id=agent.id,
        content="User asked about their day",
        metadata={"type": "conversation"}
    )
    print(f"   Memory stored: {memory_id}")

    # 4. Register a custom tool
    print("\n4. Registering custom tool...")

    async def calculator(params, context):
        operation = params.get("operation")
        a = params.get("a", 0)
        b = params.get("b", 0)

        if operation == "add":
            return {"result": a + b}
        elif operation == "subtract":
            return {"result": a - b}
        elif operation == "multiply":
            return {"result": a * b}
        elif operation == "divide":
            return {"result": a / b if b != 0 else "error"}
        return {"result": "unknown operation"}

    tool = await tools.register_tool(
        name="calculator",
        description="A simple calculator",
        schema={
            "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
            "a": {"type": "number"},
            "b": {"type": "number"}
        },
        executor=calculator
    )
    print(f"   Tool registered: {tool.name}")

    # 5. Use the tool
    print("\n5. Using calculator tool...")
    result = await tools.execute(
        tool_name="calculator",
        parameters={"operation": "add", "a": 10, "b": 5}
    )
    print(f"   Result: 10 + 5 = {result['result']['result']}")

    # 6. Governance - Create user
    print("\n6. Creating user...")
    user = await governance.create_user(
        username="demo_user",
        email="demo@agentos.io"
    )
    print(f"   User created: {user.username}")

    # 7. Check permissions
    print("\n7. Checking permissions...")
    has_perm = await governance.check_permission(
        user.id,
        "agent:create"
    )
    print(f"   User has agent:create: {has_perm}")

    print("\n" + "=" * 50)
    print("Example complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
