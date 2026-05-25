"""
Day 61: Production Deployment - Docker & Kubernetes
====================================================
Skill: Container Orchestration
Mini Project: Deploy Agent to Production

Deploy AI agents to production with Docker and Kubernetes.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ContainerConfig:
    """Docker container configuration"""
    image: str
    name: str
    ports: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceConfig:
    """Kubernetes service configuration"""
    name: str
    replicas: int = 1
    container: ContainerConfig
    port: int = 8000
    target_port: int = 8000


class DockerfileGenerator:
    """Generate Dockerfile for agents"""

    @staticmethod
    def generate(
        base_image: str = "python:3.11-slim",
        requirements: List[str] = None
    ) -> str:
        """Generate Dockerfile content"""

        deps = "\n".join(f"  {r}" for r in (requirements or []))

        return f"""FROM {base_image}

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run agent
CMD ["python", "agent.py"]
"""


class KubernetesManifest:
    """Generate Kubernetes manifests"""

    @staticmethod
    def deployment(config: ServiceConfig) -> Dict[str, Any]:
        """Generate Deployment manifest"""

        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": config.name,
                "labels": {"app": config.name}
            },
            "spec": {
                "replicas": config.replicas,
                "selector": {
                    "matchLabels": {"app": config.name}
                },
                "template": {
                    "metadata": {
                        "labels": {"app": config.name}
                    },
                    "spec": {
                        "containers": [{
                            "name": config.container.name,
                            "image": config.container.image,
                            "ports": [{
                                "containerPort": config.target_port
                            }],
                            "env": [
                                {"name": k, "value": v}
                                for k, v in config.container.environment.items()
                            ],
                            "resources": config.container.resources or {}
                        }]
                    }
                }
            }
        }

    @staticmethod
    def service(config: ServiceConfig) -> Dict[str, Any]:
        """Generate Service manifest"""

        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": config.name
            },
            "spec": {
                "selector": {"app": config.name},
                "ports": [{
                    "port": config.port,
                    "targetPort": config.target_port
                }],
                "type": "ClusterIP"
            }
        }


class DockerCompose:
    """Docker Compose configuration"""

    @staticmethod
    def generate(
        agent_config: Dict[str, Any],
        db_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate docker-compose.yml"""

        services = {
            "agent": {
                "build": ".",
                "ports": ["8000:8000"],
                "environment": {
                    "DATABASE_URL": "postgresql://db:5432/agentos",
                    "OPENAI_API_KEY": "${OPENAI_API_KEY}"
                },
                "depends_on": ["db"] if db_config else []
            }
        }

        if db_config:
            services["db"] = {
                "image": "postgres:15",
                "environment": {
                    "POSTGRES_DB": "agentos",
                    "POSTGRES_USER": "agentos",
                    "POSTGRES_PASSWORD": "agentos"
                },
                "volumes": ["db_data:/var/lib/postgresql/data"]
            }

        return {
            "version": "3.8",
            "services": services,
            "volumes": {"db_data": {}}
        }


class DeploymentManager:
    """Manage agent deployments"""

    def __init__(self):
        self.deployments: Dict[str, Dict[str, Any]] = {}

    def deploy(
        self,
        name: str,
        config: ServiceConfig,
        environment: str = "local"
    ) -> Dict[str, Any]:
        """Deploy agent"""

        deployment = {
            "name": name,
            "environment": environment,
            "config": {
                "image": config.container.image,
                "replicas": config.replicas
            },
            "status": "deploying",
            "deployed_at": datetime.now().isoformat()
        }

        self.deployments[name] = deployment

        # Simulate deployment
        deployment["status"] = "ready"

        return deployment

    def scale(self, name: str, replicas: int) -> bool:
        """Scale deployment"""
        if name in self.deployments:
            self.deployments[name]["config"]["replicas"] = replicas
            return True
        return False

    def get_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get deployment status"""
        return self.deployments.get(name)

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all deployments"""
        return list(self.deployments.values())


# Demo
def run_demo():
    print("=" * 70)
    print("Production Deployment Demo")
    print("=" * 70)

    # Generate Dockerfile
    print("\n[1] Dockerfile")
    print("-" * 40)

    dockerfile = DockerfileGenerator.generate(
        requirements=["fastapi", "uvicorn", "openai"]
    )
    print(dockerfile[:200] + "...")

    # Kubernetes manifests
    print("\n[2] Kubernetes Manifests")
    print("-" * 40)

    container = ContainerConfig(
        image="agentos/agent:latest",
        name="agent",
        ports=["8000"],
        environment={"LOG_LEVEL": "INFO"}
    )

    service = ServiceConfig(
        name="agent-service",
        replicas=3,
        container=container
    )

    deploy_manifest = KubernetesManifest.deployment(service)
    print(f"Deployment: {deploy_manifest['kind']}")

    service_manifest = KubernetesManifest.service(service)
    print(f"Service: {service_manifest['kind']}")

    # Docker Compose
    print("\n[3] Docker Compose")
    print("-" * 40)

    compose = DockerCompose.generate(
        agent_config={"port": 8000},
        db_config={"type": "postgres"}
    )
    print(f"Services: {list(compose['services'].keys())}")

    # Deployment management
    print("\n[4] Deployment Manager")
    print("-" * 40)

    manager = DeploymentManager()

    deployment = manager.deploy("my-agent", service, "production")
    print(f"Deployed: {deployment['name']} - {deployment['status']}")

    manager.scale("my-agent", 5)
    status = manager.get_status("my-agent")
    print(f"Scaled to: {status['config']['replicas']} replicas")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()