"""
Day 1: Python for JavaScript Developers
=========================================
Skill: Python Syntax & Data Structures
Mini Project: Agent Identity Parser

Converts JavaScript-style logic to Python.
Parses JSON file of "Agent Identities" and filters by permission level.
"""

import json
from typing import List, Dict, Any

# JavaScript equivalent:
# const agents = [
#   { name: "Agent1", permission: "admin" },
#   { name: "Agent2", permission: "user" }
# ];
# const adminAgents = agents.filter(a => a.permission === "admin");

# Python equivalent:
def load_agents(filepath: str) -> List[Dict[str, Any]]:
    """Load agents from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def filter_by_permission(agents: List[Dict[str, Any]], permission: str) -> List[Dict[str, Any]]:
    """Filter agents by permission level - like JS .filter()"""
    return [agent for agent in agents if agent.get('permission') == permission]

# List comprehension equivalent to JS map
def get_agent_names(agents: List[Dict[str, Any]]) -> List[str]:
    """Get all agent names - like JS .map()"""
    return [agent['name'] for agent in agents]

# Dict equivalent - JS object
agent_config = {
    "name": "ResearchAgent",
    "permission": "admin",
    "tools": ["read_file", "web_search", "send_message"]
}

if __name__ == "__main__":
    # Sample data for testing
    sample_agents = [
        {"id": "agent_001", "name": "ResearchBot", "permission": "admin", "status": "active"},
        {"id": "agent_002", "name": "DataBot", "permission": "user", "status": "active"},
        {"id": "agent_003", "name": "MailBot", "permission": "guest", "status": "inactive"},
        {"id": "agent_004", "name": "AdminBot", "permission": "admin", "status": "active"}
    ]

    # Filter by permission
    admins = filter_by_permission(sample_agents, "admin")
    print("Admin Agents:", get_agent_names(admins))

    # Using list comprehension for complex filtering
    active_admins = [a for a in sample_agents if a['permission'] == 'admin' and a['status'] == 'active']
    print("Active Admin Agents:", get_agent_names(active_admins))