"""
AgentOS - Governance Layer
Security and permission enforcement for AI agents
"""

import uuid
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum


# ============================================================================
# AGENTIC PATTERNS - Day 6 Implementation
# ============================================================================

class Tool:
    """Tool definition for Agent function calling"""

    def __init__(self, name: str, description: str, parameters: Dict, function: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.function = function

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class SubTask:
    """Sub-task for planning pattern"""

    def __init__(self, task_id: str, description: str, status: str = "pending", result: str = ""):
        self.task_id = task_id
        self.description = description
        self.status = status  # pending, in_progress, completed, failed
        self.result = result
        self.created_at = datetime.now()
        self.completed_at = None

    def complete(self, result: str):
        self.status = "completed"
        self.result = result
        self.completed_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class Review:
    """Review for reflection pattern"""

    def __init__(self, task_prompt: str, response: str, feedback: str, quality_score: float = 0.0):
        self.task_prompt = task_prompt
        self.response = response
        self.feedback = feedback
        self.quality_score = quality_score
        self.created_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "task_prompt": self.task_prompt,
            "response": self.response,
            "feedback": self.feedback,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat()
        }


class AgentRole(Enum):
    """Agent roles for multi-agent collaboration"""
    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    PLANNER = "planner"
    EXECUTOR = "executor"
    GENERAL = "general"


class Tier(Enum):
    """Organization tier levels"""
    STARTUP = "startup"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class Permission(Enum):
    """System permissions"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    EXECUTE_COMMANDS = "execute_commands"
    NETWORK_ACCESS = "network_access"
    REGISTRY_ACCESS = "registry_access"
    INSTALL_SOFTWARE = "install_software"


class AgentStatus(Enum):
    """Agent status"""
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class AuditAction(Enum):
    """Audit action status"""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    WARNING = "warning"


# Tier limits configuration
TIER_LIMITS = {
    Tier.STARTUP: {
        "max_agents": 5,
        "max_workflows": 10,
        "storage_mb": 1024,  # 1GB
        "rate_limit_per_minute": 100,
        "file_ops_per_hour": 500,
        "network_per_hour": 1000,
    },
    Tier.BUSINESS: {
        "max_agents": 25,
        "max_workflows": 100,
        "storage_mb": 51200,  # 50GB
        "rate_limit_per_minute": 1000,
        "file_ops_per_hour": 5000,
        "network_per_hour": 10000,
    },
    Tier.ENTERPRISE: {
        "max_agents": -1,  # Unlimited
        "max_workflows": -1,
        "storage_mb": -1,
        "rate_limit_per_minute": -1,
        "file_ops_per_hour": -1,
        "network_per_hour": -1,
    },
}

# Default blocked actions (auto-blocked regardless of permissions)
BLOCKED_ACTIONS = [
    "delete_system_files",
    "modify_registry",
    "install_software",
    "format_drive",
    "modify_boot_config",
]

# Actions requiring approval
REQUIRE_APPROVAL = [
    "execute_elevated_commands",
    "write_to_system_dirs",
    "modify_users",
    "change_network_config",
]


class Agent:
    """AI Agent representation with Agentic Patterns (Day 6)"""

    def __init__(self, name: str, agent_type: str, description: str = ""):
        self.id = f"agent_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.type = agent_type
        self.description = description
        self.status = AgentStatus.IDLE
        self.permissions: List[str] = []
        self.tasks_completed = 0
        self.errors = 0
        self.created_at = datetime.now()
        self.last_activity = None

        # --- Day 6: Agentic Patterns ---
        # Reflection Pattern fields
        self.last_task_prompt: str = ""
        self.last_response: str = ""
        self.reviews: List[Review] = []

        # Tool Use Pattern fields
        self.tools: List[Tool] = []
        self.tool_calls: List[Dict] = []

        # Planning Pattern fields
        self.sub_tasks: List[SubTask] = []
        self.plan: str = ""
        self.current_sub_task: Optional[SubTask] = None

        # Multi-Agent Collaboration Pattern fields
        self.role: AgentRole = AgentRole.GENERAL
        self.team_id: Optional[str] = None
        self.supervisor_id: Optional[str] = None

    # === Reflection Pattern Methods ===

    def reflect(self, task_prompt: str, response: str, quality_score: float = 0.0) -> Review:
        """
        Reflection Pattern: Self-critique and refine responses
        Analyzes the task and response to provide feedback
        """
        self.last_task_prompt = task_prompt
        self.last_response = response

        # Generate feedback based on response quality
        feedback = self._generate_feedback(task_prompt, response, quality_score)

        review = Review(task_prompt, response, feedback, quality_score)
        self.reviews.append(review)

        return review

    def _generate_feedback(self, task_prompt: str, response: str, quality_score: float) -> str:
        """Generate feedback for the response"""
        if not response:
            return "No response provided. Please provide a complete response."

        if quality_score >= 0.8:
            return f"Excellent response. Task completed successfully with high quality."
        elif quality_score >= 0.5:
            return f"Good response. Consider adding more detail or clarity to improve quality."
        else:
            return f"Response needs improvement. Consider refining the approach and adding more context."

    def review(self, task_prompt: str, response: str) -> Review:
        """
        Reflection Pattern: Review a response and provide detailed feedback
        """
        # Simple quality assessment
        quality_score = self._assess_quality(task_prompt, response)
        return self.reflect(task_prompt, response, quality_score)

    def _assess_quality(self, task_prompt: str, response: str) -> float:
        """Assess response quality (0.0 to 1.0)"""
        score = 0.5  # Base score

        # Check response length relative to task complexity
        if len(response) > 50:
            score += 0.1
        if len(response) > 200:
            score += 0.1

        # Check for task-specific keywords
        task_lower = task_prompt.lower()
        response_lower = response.lower()

        # Simple keyword matching
        key_terms = [word for word in task_lower.split() if len(word) > 4]
        matched = sum(1 for term in key_terms if term in response_lower)
        if key_terms:
            score += (matched / len(key_terms)) * 0.3

        return min(score, 1.0)

    def get_last_review(self) -> Optional[Review]:
        """Get the most recent review"""
        return self.reviews[-1] if self.reviews else None

    # === Tool Use Pattern Methods ===

    def add_tool(self, tool: Tool):
        """Tool Use Pattern: Add a tool to the agent"""
        self.tools.append(tool)

    def set_tools(self, tools: List[Tool]):
        """Tool Use Pattern: Set multiple tools"""
        self.tools = tools

    def get_available_tools_description(self) -> str:
        """Tool Use Pattern: Get description of available tools for system prompt"""
        if not self.tools:
            return "No tools available."

        tools_desc = "Available tools:\n"
        for tool in self.tools:
            tools_desc += f"- {tool.name}: {tool.description}\n"
        return tools_desc

    def execute_tool(self, tool_name: str, parameters: Dict) -> Any:
        """Tool Use Pattern: Execute a tool by name"""
        for tool in self.tools:
            if tool.name == tool_name:
                # Record the tool call
                self.tool_calls.append({
                    "tool": tool_name,
                    "parameters": parameters,
                    "timestamp": datetime.now().isoformat()
                })

                # Execute the tool function
                try:
                    result = tool.function(**parameters)
                    return result
                except Exception as e:
                    return {"error": str(e)}

        return {"error": f"Tool '{tool_name}' not found"}

    def parse_tool_calls(self, response: str) -> List[Dict]:
        """Tool Use Pattern: Parse tool calls from LLM response"""
        tool_calls = []

        # Look for tool call patterns like: [TOOL_CALL:tool_name:param1=value1]
        pattern = r'\[TOOL_CALL:(\w+):(.+?)\]'
        matches = re.findall(pattern, response)

        for tool_name, params_str in matches:
            # Parse parameters
            params = {}
            param_pattern = r'(\w+)=([^,\]]+)'
            for key, value in re.findall(param_pattern, params_str):
                params[key] = value

            tool_calls.append({
                "tool": tool_name,
                "parameters": params
            })

        return tool_calls

    # === Planning Pattern Methods ===

    def create_plan(self, task: str) -> List[SubTask]:
        """Planning Pattern: Create a plan with sub-tasks for complex objectives"""
        self.plan = task

        # Simple task decomposition
        sub_tasks = []

        # Break down task into sub-tasks
        task_parts = task.lower().split()
        task_type = ""

        if any(word in task_parts for word in ["research", "find", "search", "investigate"]):
            task_type = "research"
        if any(word in task_parts for word in ["code", "build", "create", "implement", "write"]):
            task_type = "development"
        if any(word in task_parts for word in ["test", "verify", "check", "validate"]):
            task_type = "testing"
        if any(word in task_parts for word in ["review", "analyze", "evaluate", "assess"]):
            task_type = "review"
        if any(word in task_parts for word in ["deploy", "release", "publish", "launch"]):
            task_type = "deployment"

        # Create sub-tasks based on task type
        if task_type:
            sub_task_defs = {
                "research": ["Gather requirements", "Collect relevant information", "Analyze findings"],
                "development": ["Design solution", "Implement code", "Handle edge cases"],
                "testing": ["Write test cases", "Execute tests", "Document results"],
                "review": ["Review implementation", "Provide feedback", "Suggest improvements"],
                "deployment": ["Prepare deployment", "Execute deployment", "Verify deployment"]
            }

            for i, sub_desc in enumerate(sub_task_defs.get(task_type, ["Complete task"])):
                sub_tasks.append(SubTask(f"sub_{i+1}", sub_desc))

        else:
            # Generic task breakdown
            sub_tasks.append(SubTask("sub_1", "Understand the task"))
            sub_tasks.append(SubTask("sub_2", "Plan the approach"))
            sub_tasks.append(SubTask("sub_3", "Execute the task"))
            sub_tasks.append(SubTask("sub_4", "Verify results"))

        self.sub_tasks = sub_tasks
        return sub_tasks

    def get_next_sub_task(self) -> Optional[SubTask]:
        """Planning Pattern: Get the next pending sub-task"""
        for task in self.sub_tasks:
            if task.status == "pending":
                self.current_sub_task = task
                task.status = "in_progress"
                return task
        return None

    def complete_sub_task(self, task_id: str, result: str):
        """Planning Pattern: Mark a sub-task as completed"""
        for task in self.sub_tasks:
            if task.task_id == task_id:
                task.complete(result)
                self.current_sub_task = None
                break

    def is_plan_complete(self) -> bool:
        """Planning Pattern: Check if all sub-tasks are complete"""
        return all(task.status == "completed" for task in self.sub_tasks)

    def get_plan_progress(self) -> float:
        """Planning Pattern: Get plan completion progress (0.0 to 1.0)"""
        if not self.sub_tasks:
            return 0.0
        completed = sum(1 for task in self.sub_tasks if task.status == "completed")
        return completed / len(self.sub_tasks)

    # === Multi-Agent Collaboration Pattern Fields (getters/setters) ===

    def set_role(self, role: AgentRole):
        """Multi-Agent: Set agent role"""
        self.role = role

    def join_team(self, team_id: str):
        """Multi-Agent: Join a team"""
        self.team_id = team_id

    def set_supervisor(self, supervisor_id: str):
        """Multi-Agent: Set supervisor agent"""
        self.supervisor_id = supervisor_id

    def get_team_agents(self, all_agents: List['Agent']) -> List['Agent']:
        """Multi-Agent: Get all agents in the same team"""
        if not self.team_id:
            return []
        return [a for a in all_agents if a.team_id == self.team_id]

    def get_subordinates(self, all_agents: List['Agent']) -> List['Agent']:
        """Multi-Agent: Get all agents supervised by this agent"""
        return [a for a in all_agents if a.supervisor_id == self.id]

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "status": self.status.value,
            "permissions": self.permissions,
            "tasks_completed": self.tasks_completed,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            # Day 6: Agentic Patterns
            "role": self.role.value,
            "team_id": self.team_id,
            "supervisor_id": self.supervisor_id,
            "plan": self.plan,
            "plan_progress": self.get_plan_progress(),
            "tools_available": len(self.tools),
            "tool_calls_count": len(self.tool_calls),
            "reviews_count": len(self.reviews)
        }
        return result


class Workflow:
    """Workflow representation"""

    def __init__(self, name: str, description: str = ""):
        self.id = f"wf_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.description = description
        self.nodes: List[Dict] = []
        self.status = "draft"
        self.trigger = None
        self.runs = 0
        self.created_at = datetime.now()
        self.last_run = None

    def add_node(self, node_type: str, config: Dict):
        self.nodes.append({
            "id": len(self.nodes) + 1,
            "type": node_type,
            "config": config
        })

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": self.nodes,
            "status": self.status,
            "trigger": self.trigger,
            "runs": self.runs,
            "created_at": self.created_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None
        }


class GovernanceRule:
    """Governance rule representation"""

    def __init__(self, name: str, permission: Permission, action: str, enabled: bool = True):
        self.id = uuid.uuid4().hex[:8]
        self.name = name
        self.permission = permission
        self.action = action  # "allow", "block", "require_approval"
        self.enabled = enabled

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "permission": self.permission.value,
            "action": self.action,
            "enabled": self.enabled
        }


class Organization:
    """Organization with governance"""

    def __init__(self, name: str, tier: Tier):
        self.id = f"org_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.tier = tier
        self.agents: List[Agent] = []
        self.workflows: List[Workflow] = []
        self.governance_rules: List[GovernanceRule] = []
        self.rate_limit_used = 0
        self.file_ops_used = 0
        self.network_used = 0
        self.created_at = datetime.now()
        self._init_default_rules()

    def _init_default_rules(self):
        """Initialize default governance rules"""
        # Auto-block rules
        self.add_rule("Block system file deletion", Permission.FILE_DELETE, "block")
        self.add_rule("Block registry modification", Permission.REGISTRY_ACCESS, "block")
        self.add_rule("Block software installation", Permission.INSTALL_SOFTWARE, "block")

        # Approval required
        self.add_rule("Require approval for commands", Permission.EXECUTE_COMMANDS, "require_approval")

        # Allowed by default
        self.add_rule("Allow file read", Permission.FILE_READ, "allow")
        self.add_rule("Allow file write", Permission.FILE_WRITE, "allow")
        self.add_rule("Allow network access", Permission.NETWORK_ACCESS, "allow")

    def get_limits(self) -> dict:
        """Get tier limits"""
        return TIER_LIMITS[self.tier]

    def can_add_agent(self) -> bool:
        """Check if can add more agents"""
        limits = self.get_limits()
        max_agents = limits["max_agents"]
        return max_agents == -1 or len(self.agents) < max_agents

    def can_add_workflow(self) -> bool:
        """Check if can add more workflows"""
        limits = self.get_limits()
        max_workflows = limits["max_workflows"]
        return max_workflows == -1 or len(self.workflows) < max_workflows

    def add_agent(self, name: str, agent_type: str, description: str = "",
                  permissions: List[str] = None) -> Optional[Agent]:
        """Add new agent"""
        if not self.can_add_agent():
            return None

        agent = Agent(name, agent_type, description)
        agent.permissions = permissions or ["file_read", "network_access"]
        self.agents.append(agent)
        return agent

    def add_workflow(self, name: str, description: str = "") -> Optional[Workflow]:
        """Add new workflow"""
        if not self.can_add_workflow():
            return None

        workflow = Workflow(name, description)
        self.workflows.append(workflow)
        return workflow

    def add_rule(self, name: str, permission: Permission, action: str):
        """Add governance rule"""
        rule = GovernanceRule(name, permission, action)
        self.governance_rules.append(rule)

    def check_permission(self, agent_id: str, permission: Permission) -> Tuple[bool, str]:
        """Check if agent has permission"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False, "Agent not found"

        # Check if permission is in agent's allowed list
        if permission.value not in agent.permissions:
            return False, f"Agent lacks {permission.value} permission"

        # Check governance rules
        for rule in self.governance_rules:
            if not rule.enabled:
                continue

            if rule.permission == permission:
                if rule.action == "block":
                    return False, f"Blocked by governance: {rule.name}"
                elif rule.action == "require_approval":
                    return False, f"Requires approval: {rule.name}"
                elif rule.action == "allow":
                    return True, "Allowed by governance"

        return True, "Allowed"

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None

    def check_rate_limit(self) -> Tuple[bool, str]:
        """Check rate limit"""
        limits = self.get_limits()
        rate_limit = limits["rate_limit_per_minute"]

        if rate_limit == -1:
            return True, "OK"

        if self.rate_limit_used >= rate_limit:
            return False, "Rate limit exceeded"

        self.rate_limit_used += 1
        return True, "OK"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier.value,
            "agents_count": len(self.agents),
            "workflows_count": len(self.workflows),
            "limits": self.get_limits(),
            "created_at": self.created_at.isoformat()
        }


class GovernanceEngine:
    """Main governance engine"""

    def __init__(self):
        self.organizations: Dict[str, Organization] = {}
        self.current_org: Optional[Organization] = None

    def create_organization(self, name: str, tier: Tier) -> Organization:
        """Create new organization"""
        org = Organization(name, tier)
        self.organizations[org.id] = org
        return org

    def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        return self.organizations.get(org_id)

    def delete_organization(self, org_id: str) -> bool:
        """Delete organization"""
        if org_id in self.organizations:
            del self.organizations[org_id]
            return True
        return False

    def process_action(self, org_id: str, agent_id: str, action: str,
                       details: Dict = None) -> Dict:
        """Process agent action through governance"""
        org = self.get_organization(org_id)
        if not org:
            return {"status": "error", "message": "Organization not found"}

        # Map action to permission
        permission_map = {
            "read_file": Permission.FILE_READ,
            "write_file": Permission.FILE_WRITE,
            "delete_file": Permission.FILE_DELETE,
            "execute": Permission.EXECUTE_COMMANDS,
            "network": Permission.NETWORK_ACCESS,
            "registry": Permission.REGISTRY_ACCESS,
            "install": Permission.INSTALL_SOFTWARE,
        }

        # Check rate limit first
        allowed, reason = org.check_rate_limit()
        if not allowed:
            return {
                "status": "blocked",
                "message": reason,
                "action": action,
                "details": details
            }

        # Check if action is globally blocked
        if action in BLOCKED_ACTIONS:
            return {
                "status": "blocked",
                "message": f"Action {action} is globally blocked",
                "action": action,
                "details": details
            }

        # Check permission
        permission = permission_map.get(action)
        if permission:
            allowed, reason = org.check_permission(agent_id, permission)
            if not allowed:
                return {
                    "status": "blocked",
                    "message": reason,
                    "action": action,
                    "details": details,
                    "requires_approval": "require_approval" in reason
                }

        # Check approval requirement
        if action in REQUIRE_APPROVAL:
            return {
                "status": "pending_approval",
                "message": f"Action {action} requires approval",
                "action": action,
                "details": details
            }

        return {
            "status": "allowed",
            "message": "Action permitted",
            "action": action,
            "details": details
        }

    def get_org_stats(self, org_id: str) -> Optional[Dict]:
        """Get organization statistics"""
        org = self.get_organization(org_id)
        if not org:
            return None

        limits = org.get_limits()
        return {
            "tier": org.tier.value,
            "agents": {
                "total": len(org.agents),
                "active": sum(1 for a in org.agents if a.status == AgentStatus.ACTIVE),
                "idle": sum(1 for a in org.agents if a.status == AgentStatus.IDLE),
                "errors": sum(1 for a in org.agents if a.status == AgentStatus.ERROR),
            },
            "workflows": {
                "total": len(org.workflows),
                "draft": sum(1 for w in org.workflows if w.status == "draft"),
                "running": sum(1 for w in org.workflows if w.status == "running"),
                "completed": sum(1 for w in org.workflows if w.status == "completed"),
            },
            "rate_limit": {
                "used": org.rate_limit_used,
                "limit": limits["rate_limit_per_minute"]
            },
            "limits": limits
        }


# ============================================================================
# AGENTIC PATTERNS - Day 6: Advanced Components
# ============================================================================

class PlannerAgent(Agent):
    """
    PlannerAgent - Specialized agent for planning complex tasks
    Part of Planning Pattern (Day 6)
    """

    def __init__(self, name: str, description: str = ""):
        super().__init__(name, "planner", description, AgentRole.PLANNER)
        self.planned_tasks: List[Dict] = []

    def analyze_task(self, task: str) -> Dict:
        """Analyze a complex task and create a structured plan"""
        analysis = {
            "task": task,
            "complexity": self._assess_complexity(task),
            "estimated_steps": 0,
            "recommended_tools": [],
            "potential_challenges": []
        }

        # Determine complexity
        task_lower = task.lower()

        # Count action words to estimate steps
        action_words = ["create", "build", "implement", "write", "design", "research",
                        "analyze", "test", "verify", "deploy", "review", "fix"]
        step_count = sum(1 for word in action_words if word in task_lower)
        analysis["estimated_steps"] = max(step_count, 3)

        # Recommend tools based on task
        if "code" in task_lower or "program" in task_lower or "implement" in task_lower:
            analysis["recommended_tools"].append("code_editor")
            analysis["recommended_tools"].append("file_manager")
        if "test" in task_lower:
            analysis["recommended_tools"].append("test_runner")
        if "research" in task_lower or "find" in task_lower:
            analysis["recommended_tools"].append("web_search")
        if "deploy" in task_lower:
            analysis["recommended_tools"].append("deployment_tool")

        # Identify potential challenges
        if "complex" in task_lower or "difficult" in task_lower:
            analysis["potential_challenges"].append("Task may require multiple iterations")
        if "new" in task_lower or "from scratch" in task_lower:
            analysis["potential_challenges"].append("No existing templates available")
        if "integrate" in task_lower:
            analysis["potential_challenges"].append("May require API integrations")

        return analysis

    def _assess_complexity(self, task: str) -> str:
        """Assess task complexity"""
        task_length = len(task.split())
        if task_length > 50:
            return "high"
        elif task_length > 20:
            return "medium"
        else:
            return "low"

    def create_detailed_plan(self, task: str) -> Dict:
        """Create a detailed plan with sub-tasks"""
        analysis = self.analyze_task(task)

        # Create detailed sub-tasks
        sub_tasks = []
        for i in range(analysis["estimated_steps"]):
            sub_tasks.append({
                "id": f"step_{i+1}",
                "description": f"Step {i+1}: Execute phase {i+1}",
                "status": "pending",
                "estimated_duration": "variable"
            })

        plan = {
            "main_task": task,
            "complexity": analysis["complexity"],
            "sub_tasks": sub_tasks,
            "recommended_tools": analysis["recommended_tools"],
            "challenges": analysis["potential_challenges"]
        }

        self.planned_tasks.append(plan)
        return plan


class MultiAgentSystem:
    """
    MultiAgentSystem - Manages collaboration between multiple agents
    Part of Multi-Agent Collaboration Pattern (Day 6)
    """

    def __init__(self, name: str):
        self.id = f"mas_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.agents: Dict[str, Agent] = {}
        self.teams: Dict[str, List[str]] = {}  # team_id -> agent_ids
        self.messages: List[Dict] = []
        self.created_at = datetime.now()

    def register_agent(self, agent: Agent) -> bool:
        """Register an agent in the system"""
        if agent.id in self.agents:
            return False
        self.agents[agent.id] = agent
        return True

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the system"""
        if agent_id in self.agents:
            # Remove from team if part of one
            agent = self.agents[agent_id]
            if agent.team_id and agent.team_id in self.teams:
                self.teams[agent.team_id].remove(agent_id)

            # Remove as supervisor
            for a in self.agents.values():
                if a.supervisor_id == agent_id:
                    a.supervisor_id = None

            del self.agents[agent_id]
            return True
        return False

    def create_team(self, team_id: str, agent_ids: List[str]) -> bool:
        """Create a team of agents"""
        # Verify all agents exist
        for agent_id in agent_ids:
            if agent_id not in self.agents:
                return False

        self.teams[team_id] = agent_ids

        # Assign team to agents
        for agent_id in agent_ids:
            self.agents[agent_id].team_id = team_id

        return True

    def send_message(self, from_agent_id: str, to_agent_id: str, content: str) -> Dict:
        """Send a message between agents"""
        if from_agent_id not in self.agents or to_agent_id not in self.agents:
            return {"status": "error", "message": "Agent not found"}

        message = {
            "id": f"msg_{len(self.messages) + 1}",
            "from": from_agent_id,
            "to": to_agent_id,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        self.messages.append(message)
        return {"status": "success", "message_id": message["id"]}

    def broadcast_message(self, from_agent_id: str, content: str, team_id: str = None) -> int:
        """Broadcast a message to all agents or a team"""
        if from_agent_id not in self.agents:
            return 0

        target_ids = []
        if team_id and team_id in self.teams:
            target_ids = [aid for aid in self.teams[team_id] if aid != from_agent_id]
        else:
            target_ids = [aid for aid in self.agents.keys() if aid != from_agent_id]

        count = 0
        for to_id in target_ids:
            msg = {
                "id": f"msg_{len(self.messages) + 1}",
                "from": from_agent_id,
                "to": to_id,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "read": False
            }
            self.messages.append(msg)
            count += 1

        return count

    def get_messages_for_agent(self, agent_id: str, unread_only: bool = False) -> List[Dict]:
        """Get messages for a specific agent"""
        messages = [m for m in self.messages if m["to"] == agent_id]

        if unread_only:
            messages = [m for m in messages if not m["read"]]

        return messages

    def mark_message_read(self, message_id: str) -> bool:
        """Mark a message as read"""
        for message in self.messages:
            if message["id"] == message_id:
                message["read"] = True
                return True
        return False

    def execute_workflow(self, workflow_type: str, initial_task: str) -> Dict:
        """Execute a predefined multi-agent workflow"""
        if not self.agents:
            return {"status": "error", "message": "No agents registered"}

        result = {
            "workflow": workflow_type,
            "task": initial_task,
            "steps": [],
            "completed": False
        }

        if workflow_type == "research_and_code":
            # Step 1: Research
            researcher = next((a for a in self.agents.values() if a.role == AgentRole.RESEARCHER), None)
            if researcher:
                self.send_message("system", researcher.id, initial_task)
                result["steps"].append({"step": "research", "agent": researcher.id, "status": "assigned"})

            # Step 2: Code (if researcher completed)
            coder = next((a for a in self.agents.values() if a.role == AgentRole.CODER), None)
            if coder:
                result["steps"].append({"step": "code", "agent": coder.id, "status": "pending"})

            # Step 3: Review
            reviewer = next((a for a in self.agents.values() if a.role == AgentRole.REVIEWER), None)
            if reviewer:
                result["steps"].append({"step": "review", "agent": reviewer.id, "status": "pending"})

        result["completed"] = True
        return result

    def get_team_status(self, team_id: str) -> Optional[Dict]:
        """Get status of all agents in a team"""
        if team_id not in self.teams:
            return None

        agent_ids = self.teams[team_id]
        team_agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]

        return {
            "team_id": team_id,
            "member_count": len(team_agents),
            "agents": [
                {
                    "id": a.id,
                    "name": a.name,
                    "role": a.role.value,
                    "status": a.status.value
                }
                for a in team_agents
            ]
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "agent_count": len(self.agents),
            "team_count": len(self.teams),
            "messages_count": len(self.messages),
            "created_at": self.created_at.isoformat()
        }


# Singleton instance
governance = GovernanceEngine()
