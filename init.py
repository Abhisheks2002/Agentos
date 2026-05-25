"""
AgentOS - Initialization Script
Initializes all core modules and creates demo data
"""

import sys
import os

# Add core directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core.governance import governance, Tier, AgentStatus
from core.database import db
from core.os_bridge import os_bridge
from core.task_queue import task_queue, Task, TaskPriority, TaskState, default_task_handler


def initialize_agentos():
    """Initialize AgentOS with default configuration"""
    print("Initializing AgentOS...")

    # Initialize database
    print("  - Database initialized")

    # Initialize task queue with database
    task_queue.db = db
    task_queue.max_workers = 3
    print("  - Task queue initialized")

    # Create demo organization
    org = governance.create_organization("Acme Corp", Tier.ENTERPRISE)
    print(f"  - Created organization: {org.name} ({org.tier.value})")

    # Add demo agents
    agent1 = org.add_agent(
        "DataProcessor",
        "Data Processing",
        "Processes business data and generates reports",
        ["file_read", "file_write", "network_access"]
    )

    agent2 = org.add_agent(
        "FileSync",
        "File Management",
        "Syncs files to cloud storage",
        ["file_read", "file_write"]
    )

    agent3 = org.add_agent(
        "EmailAssistant",
        "Communication",
        "Manages email communications",
        ["network_access"]
    )

    print(f"  - Created {len(org.agents)} agents")

    # Add demo workflows
    wf1 = org.add_workflow("Daily Report", "Generate daily reports")
    wf1.add_node("trigger", {"type": "schedule", "cron": "0 9 * * *"})
    wf1.add_node("action", {"type": "query_data", "source": "database"})
    wf1.add_node("action", {"type": "generate_report", "format": "pdf"})
    wf1.add_node("notify", {"type": "email", "to": "team@example.com"})

    wf2 = org.add_workflow("File Backup", "Backup important files")
    wf2.add_node("trigger", {"type": "schedule", "cron": "0 2 * * *"})
    wf2.add_node("action", {"type": "list_files", "path": "/data"})
    wf2.add_node("condition", {"check": "file_count > 0"})
    wf2.add_node("action", {"type": "compress", "format": "zip"})
    wf2.add_node("action", {"type": "upload", "destination": "backup-server"})

    print(f"  - Created {len(org.workflows)} workflows")

    # Create demo tasks for agents
    print("  - Creating demo tasks...")
    _create_demo_tasks(org)

    # Get system info
    sys_info = os_bridge.get_system_info()
    print(f"  - Platform: {sys_info.get('platform', 'unknown')}")

    # Create workspace directory
    workspace = os_bridge.workspace_dir
    os.makedirs(workspace, exist_ok=True)
    print(f"  - Workspace: {workspace}")

    # Save to database
    db.save_organization(org.to_dict())
    for agent in org.agents:
        db.save_agent({
            "id": agent.id,
            "org_id": org.id,
            "name": agent.name,
            "type": agent.type,
            "description": agent.description,
            "status": agent.status.value,
            "permissions": agent.permissions,
            "tasks_completed": agent.tasks_completed,
            "errors": agent.errors,
            "created_at": agent.created_at.isoformat(),
            "last_activity": agent.last_activity.isoformat() if agent.last_activity else None
        })
    for workflow in org.workflows:
        db.save_workflow(workflow.to_dict())

    # Create demo tasks
    print("\n  Creating demo tasks...")

    # Start task queue with handler
    task_queue.start(default_task_handler)

    # Add demo tasks
    demo_tasks = [
        {
            "agent_id": agent1.id,
            "task_type": "file_read",
            "payload": {"path": "/data/report.txt"},
            "priority": TaskPriority.HIGH
        },
        {
            "agent_id": agent1.id,
            "task_type": "process_data",
            "payload": {"source": "database", "query": "SELECT * FROM users"},
            "priority": TaskPriority.NORMAL
        },
        {
            "agent_id": agent2.id,
            "task_type": "file_write",
            "payload": {"path": "/data/backup.json", "content": '{"status": "backed up"}'},
            "priority": TaskPriority.NORMAL
        },
        {
            "agent_id": agent2.id,
            "task_type": "send_notification",
            "payload": {"to": "admin@example.com", "message": "Backup complete"},
            "priority": TaskPriority.LOW
        },
        {
            "agent_id": agent3.id,
            "task_type": "process_data",
            "payload": {"operation": "analyze", "data": "email_stats"},
            "priority": TaskPriority.NORMAL
        }
    ]

    for task_config in demo_tasks:
        task = Task(
            agent_id=task_config["agent_id"],
            task_type=task_config["task_type"],
            payload=task_config["payload"],
            priority=task_config["priority"]
        )
        task_queue.enqueue(task)
        print(f"    - Enqueued: {task.task_type} (priority: {task.priority.name})")

    print(f"\nAgentOS initialized successfully!")
    print(f"  Organization ID: {org.id}")
    print(f"  Agent IDs: {[a.id for a in org.agents]}")
    print(f"  Workflow IDs: {[w.id for w in org.workflows]}")

    return org


def test_governance(org):
    """Test governance enforcement"""
    print("\n--- Testing Governance ---")

    # Test 1: Allowed action
    result = governance.process_action(org.id, org.agents[0].id, "read_file", {"path": "/data/file.txt"})
    print(f"1. Read file: {result['status']}")

    # Test 2: Blocked action
    result = governance.process_action(org.id, org.agents[0].id, "execute", {"command": "rm -rf /"})
    print(f"2. Execute dangerous: {result['status']} - {result.get('message', '')}")

    # Test 3: Registry access (blocked by default)
    result = governance.process_action(org.id, org.agents[0].id, "registry", {})
    print(f"3. Registry access: {result['status']} - {result.get('message', '')}")


def test_os_bridge():
    """Test OS Bridge operations"""
    print("\n--- Testing OS Bridge ---")

    # Test system info
    info = os_bridge.get_system_info()
    print(f"1. System info: {info.get('platform', 'unknown')}")

    # Test file write
    test_file = os.path.join(os_bridge.workspace_dir, "test.txt")
    result = os_bridge.write_file(test_file, "Hello from AgentOS!")
    print(f"2. Write file: {result.get('success', False)}")

    # Test file read
    result = os_bridge.read_file(test_file)
    print(f"3. Read file: {result.get('success', False)}")

    # Test directory list
    result = os_bridge.list_directory()
    print(f"4. List directory: {result.get('success', False)}")


def test_task_queue():
    """Test Task Queue operations"""
    print("\n--- Testing Task Queue ---")

    # Wait a moment for tasks to process
    import time
    time.sleep(2)

    # Get queue stats
    stats = task_queue.get_queue_stats()
    print(f"1. Queue stats: {stats}")

    # Get task by ID (first task)
    if task_queue._tasks:
        first_task_id = list(task_queue._tasks.keys())[0]
        task = task_queue.get_task_by_id(first_task_id)
        print(f"2. First task: {task.task_type} - {task.state.value}")

    # Get tasks by agent
    if org.agents:
        agent_tasks = task_queue.get_tasks_by_agent(org.agents[0].id)
        print(f"3. Agent tasks count: {len(agent_tasks)}")

    # Get database task stats
    db_stats = db.get_task_stats()
    print(f"4. DB task stats: {db_stats}")


if __name__ == "__main__":
    # Initialize
    org = initialize_agentos()

    # Run tests
    test_governance(org)
    test_os_bridge()

    print("\nAgentOS is ready!")
    print("Run 'node server.js' to start the API server")
    print("Or run 'electron .' to start the desktop app")
