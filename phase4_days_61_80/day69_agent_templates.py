"""
Day 69: Custom Agent Templates
================================
Creating reusable agent templates for common use cases.

Key Concepts:
- Template inheritance
- Configuration schemas
- Template composition
- Default behaviors
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid


class AgentCapability(Enum):
    """Agent capabilities"""
    TEXT_GENERATION = "text_generation"
    ANALYSIS = "analysis"
    CODE_GENERATION = "code_generation"
    DATA_PROCESSING = "data_processing"
    IMAGE_ANALYSIS = "image_analysis"
    API_INTEGRATION = "api_integration"
    FILE_HANDLING = "file_handling"


@dataclass
class TemplateConfig:
    """Configuration for an agent template"""
    name: str
    description: str
    capabilities: List[AgentCapability]
    default_params: Dict[str, Any] = field(default_factory=dict)
    system_prompt: str = ""
    tools: List[str] = field(default_factory=list)
    memory_limit_mb: int = 256
    timeout_seconds: int = 60


@dataclass
class AgentInstance:
    """An instantiated agent from a template"""
    agent_id: str
    template_id: str
    name: str
    config: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "idle"


class AgentTemplate:
    """
    Agent Template
    ==============

    Reusable agent configuration.
    """

    def __init__(self, template_id: str, config: TemplateConfig):
        self.template_id = template_id
        self.config = config
        self._instances: Dict[str, AgentInstance] = {}

    def create_instance(
        self,
        name: str,
        overrides: Dict[str, Any] = None
    ) -> AgentInstance:
        """Create an agent instance from this template"""
        # Merge config with overrides
        config = {**self.config.default_params, **(overrides or {})}

        instance = AgentInstance(
            agent_id=str(uuid.uuid4()),
            template_id=self.template_id,
            name=name,
            config=config
        )

        self._instances[instance.agent_id] = instance
        return instance

    def get_instance(self, agent_id: str) -> Optional[AgentInstance]:
        """Get instance by ID"""
        return self._instances.get(agent_id)

    def list_instances(self) -> List[AgentInstance]:
        """List all instances"""
        return list(self._instances.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get template statistics"""
        return {
            "template_id": self.template_id,
            "name": self.config.name,
            "capabilities": [c.value for c in self.config.capabilities],
            "instance_count": len(self._instances)
        }


class TemplateRegistry:
    """
    Template Registry
    =================

    Manages agent templates and provides template discovery.
    """

    # Pre-built templates
    BUILT_IN_TEMPLATES = {
        "analysis": TemplateConfig(
            name="Analysis Agent",
            description="Agent specialized in data analysis",
            capabilities=[AgentCapability.ANALYSIS, AgentCapability.DATA_PROCESSING],
            default_params={"max_results": 100, "confidence_threshold": 0.8},
            system_prompt="You are a data analysis agent. Analyze the provided data and provide insights.",
            tools=["analyze", "visualize", "report"]
        ),
        "coder": TemplateConfig(
            name="Code Generation Agent",
            description="Agent specialized in code generation",
            capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.TEXT_GENERATION],
            default_params={"language": "python", "max_lines": 500},
            system_prompt="You are a code generation agent. Generate clean, well-documented code.",
            tools=["generate", "review", "test"]
        ),
        "assistant": TemplateConfig(
            name="General Assistant",
            description="General purpose assistant agent",
            capabilities=[AgentCapability.TEXT_GENERATION, AgentCapability.API_INTEGRATION],
            default_params={"temperature": 0.7, "max_tokens": 2000},
            system_prompt="You are a helpful assistant.",
            tools=["chat", "search", "compute"]
        ),
        "file_processor": TemplateConfig(
            name="File Processing Agent",
            description="Agent specialized in file handling",
            capabilities=[AgentCapability.FILE_HANDLING, AgentCapability.DATA_PROCESSING],
            default_params={"max_file_size_mb": 10, "allowed_formats": ["txt", "csv", "json"]},
            system_prompt="You are a file processing agent. Handle files efficiently and accurately.",
            tools=["read", "write", "transform"]
        ),
        "api_integration": TemplateConfig(
            name="API Integration Agent",
            description="Agent for API integration",
            capabilities=[AgentCapability.API_INTEGRATION, AgentCapability.TEXT_GENERATION],
            default_params={"timeout": 30, "retries": 3},
            system_prompt="You are an API integration agent. Handle API calls and data transformations.",
            tools=["call", "transform", "validate"]
        )
    }

    def __init__(self):
        self.templates: Dict[str, AgentTemplate] = {}
        self._init_builtin_templates()

    def _init_builtin_templates(self):
        """Initialize built-in templates"""
        for template_id, config in self.BUILT_IN_TEMPLATES.items():
            self.templates[template_id] = AgentTemplate(template_id, config)

    def register_template(
        self,
        template_id: str,
        config: TemplateConfig
    ) -> AgentTemplate:
        """Register a custom template"""
        template = AgentTemplate(template_id, config)
        self.templates[template_id] = template
        return template

    def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates"""
        return [
            {
                "template_id": tid,
                "name": t.config.name,
                "description": t.config.description,
                "capabilities": [c.value for c in t.config.capabilities]
            }
            for tid, t in self.templates.items()
        ]

    def find_templates(
        self,
        capability: AgentCapability = None
    ) -> List[AgentTemplate]:
        """Find templates by capability"""
        results = []
        for template in self.templates.values():
            if capability is None or capability in template.config.capabilities:
                results.append(template)
        return results

    def create_agent(
        self,
        template_id: str,
        name: str,
        overrides: Dict[str, Any] = None
    ) -> Optional[AgentInstance]:
        """Create agent from template"""
        template = self.get_template(template_id)
        if not template:
            return None

        return template.create_instance(name, overrides)

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_instances = sum(
            len(t.list_instances())
            for t in self.templates.values()
        )

        return {
            "total_templates": len(self.templates),
            "total_instances": total_instances,
            "templates": [
                t.get_stats() for t in self.templates.values()
            ]
        }


# Demo
async def main():
    print("=" * 60)
    print("Day 69: Custom Agent Templates")
    print("=" * 60)

    registry = TemplateRegistry()

    # List available templates
    print("\nAvailable templates:")
    for t in registry.list_templates():
        print(f"  - {t['name']} ({t['template_id']})")
        print(f"    Capabilities: {', '.join(t['capabilities'])}")

    # Find templates by capability
    print("\nTemplates with ANALYSIS capability:")
    analysis_templates = registry.find_templates(AgentCapability.ANALYSIS)
    for t in analysis_templates:
        print(f"  - {t.config.name}")

    # Create agent from template
    print("\nCreating agents from templates:")
    agent1 = registry.create_agent(
        "coder",
        "My Code Bot",
        {"language": "javascript", "max_lines": 1000}
    )
    print(f"  - Created: {agent1.name} (from coder template)")

    agent2 = registry.create_agent(
        "analysis",
        "Data Analyzer",
        {"max_results": 500}
    )
    print(f"  - Created: {agent2.name} (from analysis template)")

    # Register custom template
    custom_config = TemplateConfig(
        name="Custom ETL Agent",
        description="Custom agent for ETL operations",
        capabilities=[
            AgentCapability.DATA_PROCESSING,
            AgentCapability.FILE_HANDLING
        ],
        default_params={"batch_size": 100, "parallel": True},
        system_prompt="You are an ETL agent.",
        tools=["extract", "transform", "load"]
    )

    custom_template = registry.register_template("etl_agent", custom_config)
    print(f"\nRegistered custom template: {custom_config.name}")

    # Create from custom template
    etl_agent = custom_template.create_instance("ETL Pipeline 1")
    print(f"Created from custom: {etl_agent.name}")

    # Registry stats
    stats = registry.get_stats()
    print(f"\nRegistry stats:")
    print(f"  Total templates: {stats['total_templates']}")
    print(f"  Total instances: {stats['total_instances']}")


if __name__ == "__main__":
    asyncio.run(main())