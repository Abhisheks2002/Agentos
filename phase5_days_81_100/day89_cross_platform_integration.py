"""
Day 89: Agent Cross-Platform Integration
=========================================

Implementing cross-platform capabilities for AI agents including
Windows, macOS, and Linux support with platform-specific optimizations.

Key Concepts:
- Platform Abstraction
- Native API Integration
- Cross-Platform File Operations
- Platform-Specific Features
- Universal Agent Deployment
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import platform
import os


class Platform(Enum):
    """Supported platforms"""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


class Architecture(Enum):
    """System architectures"""
    X64 = "x64"
    ARM64 = "arm64"
    X86 = "x86"
    UNIVERSAL = "universal"


@dataclass
class PlatformInfo:
    """Platform information"""
    platform: Platform
    architecture: Architecture
    os_version: str
    hostname: str
    cpu_count: int
    memory_total: int
    python_version: str
    capabilities: List[str] = field(default_factory=list)


@dataclass
class PlatformService:
    """Platform-specific service capability"""
    service_name: str
    available: bool
    version: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)


class PlatformDetector:
    """
    Platform Detection
    ===================

    Detects platform and capabilities.
    """

    def __init__(self):
        self.info = self._detect_platform()
        self._detect_capabilities()

    def _detect_platform(self) -> PlatformInfo:
        """Detect current platform"""
        system = platform.system().lower()

        if "windows" in system:
            platform_type = Platform.WINDOWS
        elif "darwin" in system:
            platform_type = Platform.MACOS
        elif "linux" in system:
            platform_type = Platform.LINUX
        else:
            platform_type = Platform.UNKNOWN

        # Detect architecture
        arch = platform.machine().lower()
        if "x86_64" in arch or "amd64" in arch:
            architecture = Architecture.X64
        elif "arm64" in arch or "aarch64" in arch:
            architecture = Architecture.ARM64
        elif "x86" in arch or "i386" in arch:
            architecture = Architecture.X86
        else:
            architecture = Architecture.UNIVERSAL

        # Get memory
        try:
            import psutil
            memory = int(psutil.virtual_memory().total / (1024 * 1024 * 1024))  # GB
        except ImportError:
            memory = 0

        return PlatformInfo(
            platform=platform_type,
            architecture=architecture,
            os_version=platform.version(),
            hostname=platform.node(),
            cpu_count=os.cpu_count() or 1,
            memory_total=memory,
            python_version=platform.python_version()
        )

    def _detect_capabilities(self):
        """Detect platform capabilities"""
        self.info.capabilities = []

        # File system
        self.info.capabilities.append("file_operations")

        # Process management
        self.info.capabilities.append("process_management")

        # Network
        self.info.capabilities.append("network_operations")

        # Platform-specific
        if self.info.platform == Platform.WINDOWS:
            self.info.capabilities.extend(["registry", "wmi", "win32_api", "powershell"])
        elif self.info.platform == Platform.MACOS:
            self.info.capabilities.extend(["keychain", "launchd", "system_preferences"])
        elif self.info.platform == Platform.LINUX:
            self.info.capabilities.extend(["systemd", "docker", "apt"])

    def is_platform(self, platform: Platform) -> bool:
        """Check if running on specific platform"""
        return self.info.platform == platform

    def supports_feature(self, feature: str) -> bool:
        """Check if platform supports a feature"""
        return feature in self.info.capabilities


class FileSystemAbstraction:
    """
    Cross-Platform File System
    ===========================

    Unified file operations across platforms.
    """

    def __init__(self):
        self.detector = PlatformDetector()
        self.home_dir = os.path.expanduser("~")
        self.temp_dir = os.path.tempdir

    def normalize_path(self, path: str) -> str:
        """Normalize path for current platform"""
        if not path:
            return ""

        # Convert forward slashes to backslashes on Windows
        if self.detector.is_platform(Platform.WINDOWS):
            path = path.replace("/", "\\")

        return os.path.normpath(path)

    def get_agent_workspace(self, agent_id: str) -> str:
        """Get agent workspace directory"""
        workspace = os.path.join(self.home_dir, ".agentos", "agents", agent_id)
        os.makedirs(workspace, exist_ok=True)
        return workspace

    def get_config_dir(self) -> str:
        """Get configuration directory"""
        if self.detector.is_platform(Platform.WINDOWS):
            base = os.environ.get("APPDATA", os.path.join(self.home_dir, "AppData", "Roaming"))
        elif self.detector.is_platform(Platform.MACOS):
            base = os.path.join(self.home_dir, "Library", "Application Support")
        else:
            base = os.environ.get("XDG_CONFIG_HOME", os.path.join(self.home_dir, ".config"))

        config_dir = os.path.join(base, "AgentOS")
        os.makedirs(config_dir, exist_ok=True)
        return config_dir

    def get_log_dir(self) -> str:
        """Get log directory"""
        if self.detector.is_platform(Platform.WINDOWS):
            base = os.environ.get("LOCALAPPDATA", os.path.join(self.home_dir, "AppData", "Local"))
        elif self.detector.is_platform(Platform.MACOS):
            base = os.path.join(self.home_dir, "Library", "Logs")
        else:
            base = "/var/log"

        log_dir = os.path.join(base, "AgentOS")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir

    def list_drives(self) -> List[str]:
        """List available drives (Windows)"""
        if self.detector.is_platform(Platform.WINDOWS):
            import string
            drives = []
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(drive)
            return drives
        return ["/"]


class ProcessManager:
    """
    Cross-Platform Process Management
    ====================================

    Unified process operations across platforms.
    """

    def __init__(self):
        self.detector = PlatformDetector()

    async def execute_command(self, command: str, shell: bool = True) -> Dict[str, Any]:
        """Execute a command on the current platform"""
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else ""
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }

    def get_shell(self) -> str:
        """Get default shell for platform"""
        if self.detector.is_platform(Platform.WINDOWS):
            return "cmd.exe"
        elif self.detector.is_platform(Platform.MACOS):
            return "/bin/zsh"
        return "/bin/bash"

    def get_env_vars(self) -> Dict[str, str]:
        """Get environment variables"""
        return dict(os.environ)

    def get_platform_commands(self) -> Dict[str, List[str]]:
        """Get platform-specific system commands"""
        if self.detector.is_platform(Platform.WINDOWS):
            return {
                "process_list": ["tasklist"],
                "network_status": ["netstat", "-an"],
                "disk_usage": ["wmic", "logicaldisk", "get", "size,freespace,caption"],
                "service_list": ["sc", "query"],
                "user_list": ["net", "user"]
            }
        elif self.detector.is_platform(Platform.MACOS):
            return {
                "process_list": ["ps", "-aux"],
                "network_status": ["lsof", "-i"],
                "disk_usage": ["df", "-h"],
                "service_list": ["launchctl", "list"],
                "user_list": ["dscl", ".", "list", "/Users"]
            }
        else:
            return {
                "process_list": ["ps", "-aux"],
                "network_status": ["ss", "-tuln"],
                "disk_usage": ["df", "-h"],
                "service_list": ["systemctl", "list-units"],
                "user_list": ["getent", "passwd"]
            }


class NetworkManager:
    """
    Cross-Platform Network Operations
    ====================================

    Unified network operations across platforms.
    """

    def __init__(self):
        self.detector = PlatformDetector()

    def get_hostname(self) -> str:
        """Get system hostname"""
        return platform.node()

    def get_ip_addresses(self) -> Dict[str, List[str]]:
        """Get IP addresses"""
        addresses = {"ipv4": [], "ipv6": []}

        try:
            import socket
            hostname = socket.gethostname()
            ipv4 = socket.gethostbyname(hostname)
            addresses["ipv4"].append(ipv4)
        except:
            pass

        # Try to get all interfaces
        try:
            import subprocess
            if self.detector.is_platform(Platform.WINDOWS):
                result = subprocess.run(["ipconfig"], capture_output=True, text=True)
            else:
                result = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True)

            # Parse output (simplified)
            lines = result.stdout.split("\n")
            for line in lines:
                if "inet " in line:
                    ip = line.split()[1].split("/")[0]
                    if ip not in addresses["ipv4"]:
                        addresses["ipv4"].append(ip)
        except:
            pass

        return addresses

    def check_connectivity(self, host: str = "8.8.8.8") -> bool:
        """Check internet connectivity"""
        try:
            import socket
            socket.create_connection((host, 53), timeout=3)
            return True
        except:
            return False


class PlatformServiceManager:
    """
    Platform Service Management
    ============================

    Manages platform-specific services.
    """

    def __init__(self):
        self.detector = PlatformDetector()
        self.services: Dict[str, PlatformService] = {}
        self._detect_services()

    def _detect_services(self):
        """Detect available platform services"""
        if self.detector.is_platform(Platform.WINDOWS):
            self._detect_windows_services()
        elif self.detector.is_platform(Platform.MACOS):
            self._detect_macos_services()
        elif self.detector.is_platform(Platform.LINUX):
            self._detect_linux_services()

    def _detect_windows_services(self):
        """Detect Windows services"""
        self.services["Windows Defender"] = PlatformService(
            service_name="Windows Defender",
            available=True,
            version="4.18"
        )
        self.services["Windows Update"] = PlatformService(
            service_name="Windows Update",
            available=True
        )
        self.services["PowerShell"] = PlatformService(
            service_name="PowerShell",
            available=True,
            version=platform.version()
        )

    def _detect_macos_services(self):
        """Detect macOS services"""
        self.services["Gatekeeper"] = PlatformService(
            service_name="Gatekeeper",
            available=True
        )
        self.services["Firewall"] = PlatformService(
            service_name="Firewall",
            available=True
        )
        self.services["XProtect"] = PlatformService(
            service_name="XProtect",
            available=True
        )

    def _detect_linux_services(self):
        """Detect Linux services"""
        self.services["systemd"] = PlatformService(
            service_name="systemd",
            available=True
        )
        self.services["firewalld"] = PlatformService(
            service_name="firewalld",
            available=os.path.exists("/usr/bin/firewalld")
        )
        self.services["docker"] = PlatformService(
            service_name="docker",
            available=os.path.exists("/usr/bin/docker")
        )

    def get_service(self, name: str) -> Optional[PlatformService]:
        """Get service by name"""
        return self.services.get(name)

    def list_services(self) -> List[PlatformService]:
        """List all services"""
        return list(self.services.values())


class CrossPlatformAgent:
    """
    Cross-Platform Agent
    ====================

    Agent that operates across platforms.
    """

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.detector = PlatformDetector()
        self.fs = FileSystemAbstraction()
        self.process = ProcessManager()
        self.network = NetworkManager()
        self.services = PlatformServiceManager()

    def get_platform_info(self) -> PlatformInfo:
        """Get platform information"""
        return self.detector.info

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task on current platform"""
        task_type = task.get("type", "command")

        if task_type == "command":
            return await self.process.execute_command(task.get("command", ""))
        elif task_type == "file":
            return self._handle_file_task(task)
        elif task_type == "network":
            return self._handle_network_task(task)

        return {"error": "Unknown task type"}

    def _handle_file_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file operation task"""
        operation = task.get("operation", "read")
        path = task.get("path", "")

        path = self.fs.normalize_path(path)

        if operation == "read":
            try:
                with open(path, "r") as f:
                    return {"success": True, "content": f.read()}
            except Exception as e:
                return {"success": False, "error": str(e)}
        elif operation == "write":
            try:
                with open(path, "w") as f:
                    f.write(task.get("content", ""))
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        elif operation == "list":
            try:
                files = os.listdir(path)
                return {"success": True, "files": files}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"error": "Unknown operation"}

    def _handle_network_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle network task"""
        operation = task.get("operation", "status")

        if operation == "status":
            return {
                "hostname": self.network.get_hostname(),
                "ip_addresses": self.network.get_ip_addresses(),
                "connected": self.network.check_connectivity()
            }

        return {"error": "Unknown network operation"}


async def main():
    """Demonstrate Cross-Platform Integration"""
    print("=" * 60)
    print("Agent Cross-Platform Integration - Day 89")
    print("=" * 60)

    # Initialize cross-platform agent
    agent = CrossPlatformAgent("agent-001", "Platform Agent")

    # Display platform info
    print("\n[1] Platform Detection")
    print("-" * 40)
    info = agent.get_platform_info()
    print(f"Platform: {info.platform.value}")
    print(f"Architecture: {info.architecture.value}")
    print(f"OS Version: {info.os_version}")
    print(f"Hostname: {info.hostname}")
    print(f"CPU Count: {info.cpu_count}")
    print(f"Memory: {info.memory_total} GB")
    print(f"Python: {info.python_version}")
    print(f"Capabilities: {', '.join(info.capabilities)}")

    # File system paths
    print("\n[2] Platform-Specific Paths")
    print("-" * 40)
    print(f"Home: {agent.fs.home_dir}")
    print(f"Config: {agent.fs.get_config_dir()}")
    print(f"Logs: {agent.fs.get_log_dir()}")

    workspace = agent.fs.get_agent_workspace(agent.agent_id)
    print(f"Workspace: {workspace}")

    if agent.detector.is_platform(Platform.WINDOWS):
        print(f"Drives: {agent.fs.list_drives()}")

    # Process management
    print("\n[3] Process Management")
    print("-" * 40)
    print(f"Default Shell: {agent.process.get_shell()}")

    commands = agent.process.get_platform_commands()
    print(f"Available commands:")
    for cmd_type, cmd_list in commands.items():
        print(f"  {cmd_type}: {cmd_list}")

    # Network
    print("\n[4] Network Information")
    print("-" * 40)
    network_info = await agent.execute_task({"type": "network", "operation": "status"})
    print(f"Hostname: {network_info.get('hostname')}")
    print(f"IP Addresses: {network_info.get('ip_addresses')}")
    print(f"Connected: {network_info.get('connected')}")

    # Platform services
    print("\n[5] Platform Services")
    print("-" * 40)
    for service in agent.services.list_services():
        status = "Available" if service.available else "Unavailable"
        version = f" (v{service.version})" if service.version else ""
        print(f"  {service.service_name}: {status}{version}")

    # Execute test command
    print("\n[6] Execute Platform Command")
    print("-" * 40)
    if agent.detector.is_platform(Platform.WINDOWS):
        result = await agent.process.execute_command("echo %USERNAME%")
    else:
        result = await agent.process.execute_command("echo $USER")

    print(f"Command output: {result.get('stdout', '').strip()}")
    print(f"Success: {result.get('success')}")

    # Test file operation
    print("\n[7] File Operations")
    print("-" * 40)
    test_path = os.path.join(workspace, "test.txt")

    write_result = await agent.execute_task({
        "type": "file",
        "operation": "write",
        "path": test_path,
        "content": "Hello from Cross-Platform Agent!"
    })
    print(f"Write: {write_result.get('success')}")

    read_result = await agent.execute_task({
        "type": "file",
        "operation": "read",
        "path": test_path
    })
    print(f"Read: {read_result.get('success')}")
    print(f"Content: {read_result.get('content', '').strip()}")

    print("\n" + "=" * 60)
    print("Cross-Platform Integration complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())