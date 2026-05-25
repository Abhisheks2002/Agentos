"""
AgentOS - OS Bridge Layer
Provides secure interface between AI Agents and Host OS
Supports Windows and macOS
"""

import os
import sys
import subprocess
import json
import hashlib
import platform
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import urllib.request
import urllib.error
import urllib.parse
import threading
import time

# File watching support (optional)
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"


class SecurityError(Exception):
    """Raised when an operation is blocked by security rules"""
    pass


class OSBridge:
    """
    Secure OS Bridge for AgentOS
    Provides controlled access to file system, processes, and network
    """

    def __init__(self, workspace_dir: str = None):
        self.platform = platform.system()
        self.workspace_dir = workspace_dir or self._get_default_workspace()
        self.allowed_paths = [self.workspace_dir]
        self.dangerous_patterns = self._get_dangerous_patterns()
        self.blocked_commands = self._get_blocked_commands()

    def _get_default_workspace(self) -> str:
        """Get default workspace directory"""
        if IS_WINDOWS:
            base = os.environ.get('USERPROFILE', 'C:\\')
            return os.path.join(base, 'AgentOS_Workspace')
        else:
            base = os.environ.get('HOME', '/tmp')
            return os.path.join(base, 'AgentOS_Workspace')

    def _get_dangerous_patterns(self) -> List[str]:
        """Patterns that indicate dangerous paths"""
        patterns = [
            'C:\\Windows\\System32',
            'C:\\Windows\\SysWOW64',
            '/System',
            '/bin',
            '/usr/bin',
            '/usr/sbin',
            '/private/etc',
            '/Library/System',
            '.ssh',
            '.aws',
            '.npm',
            'node_modules',
            '__pycache__',
            '.git/objects',
        ]
        if IS_WINDOWS:
            patterns.extend([
                'C:\\Program Files',
                'C:\\Program Files (x86)',
                'C:\\Windows',
            ])
        return patterns

    def _get_blocked_commands(self) -> List[str]:
        """Commands that are always blocked"""
        return [
            'rm -rf /',
            'rmdir /s /q',
            'del /f /s /q',
            'format',
            'diskpart',
            'reg delete',
            'reg add',
            'shutdown',
            'restart',
            'reboot',
            'dd if=',
            'mkfs',
            ':(){ :|:& };:',
            'chmod 777 /',
            'chown -R',
        ]

    def _is_path_safe(self, path: str) -> Tuple[bool, str]:
        """Check if path is safe to access"""
        try:
            # Resolve to absolute path
            abs_path = os.path.abspath(path)

            # Check against dangerous patterns
            for pattern in self.dangerous_patterns:
                if pattern.lower() in abs_path.lower():
                    return False, f"Path contains protected directory: {pattern}"

            # Check workspace boundary
            if not abs_path.startswith(self.workspace_dir):
                return False, f"Path outside workspace: {abs_path}"

            return True, "OK"
        except Exception as e:
            return False, f"Path validation error: {str(e)}"

    def _check_command_safety(self, command: str) -> Tuple[bool, str]:
        """Check if command is safe to execute"""
        cmd_lower = command.lower()

        # Check blocked commands
        for blocked in self.blocked_commands:
            if blocked.lower() in cmd_lower:
                return False, f"Command blocked: {blocked}"

        # Check for suspicious patterns
        suspicious = ['sudo', 'su -', 'eval ', 'exec ', 'system(']
        if any(s in cmd_lower for s in suspicious):
            return False, "Suspicious command pattern detected"

        return True, "OK"

    # ============== File Operations ==============

    def read_file(self, path: str, encoding: str = 'utf-8') -> Dict:
        """Read file contents with security checks"""
        safe, reason = self._is_path_safe(path)
        if not safe:
            raise SecurityError(f"Read blocked: {reason}")

        if not os.path.exists(path):
            return {"success": False, "error": "File not found"}

        if not os.path.isfile(path):
            return {"success": False, "error": "Path is not a file"}

        try:
            # Check file size (limit to 10MB)
            size = os.path.getsize(path)
            if size > 10 * 1024 * 1024:
                return {"success": False, "error": "File too large (max 10MB)"}

            with open(path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()

            return {
                "success": True,
                "path": path,
                "content": content,
                "size": size,
                "modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, path: str, content: str, encoding: str = 'utf-8') -> Dict:
        """Write file with security checks"""
        safe, reason = self._is_path_safe(path)
        if not safe:
            raise SecurityError(f"Write blocked: {reason}")

        try:
            # Create parent directories if needed
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)

            with open(path, 'w', encoding=encoding) as f:
                f.write(content)

            return {
                "success": True,
                "path": path,
                "size": len(content),
                "created": not os.path.exists(path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_directory(self, path: str = None) -> Dict:
        """List directory contents"""
        target = path or self.workspace_dir
        safe, reason = self._is_path_safe(target)
        if not safe:
            raise SecurityError(f"List blocked: {reason}")

        if not os.path.exists(target):
            return {"success": False, "error": "Directory not found"}

        if not os.path.isdir(target):
            return {"success": False, "error": "Path is not a directory"}

        try:
            entries = []
            for entry in os.listdir(target):
                entry_path = os.path.join(target, entry)
                stat = os.stat(entry_path)
                entries.append({
                    "name": entry,
                    "type": "directory" if os.path.isdir(entry_path) else "file",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

            return {
                "success": True,
                "path": target,
                "entries": entries
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_file(self, path: str) -> Dict:
        """Delete file with safety checks"""
        safe, reason = self._is_path_safe(path)
        if not safe:
            raise SecurityError(f"Delete blocked: {reason}")

        if not os.path.exists(path):
            return {"success": False, "error": "File not found"}

        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                import shutil
                shutil.rmtree(path)

            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_file_info(self, path: str) -> Dict:
        """Get file metadata"""
        safe, reason = self._is_path_safe(path)
        if not safe:
            raise SecurityError(f"Info blocked: {reason}")

        if not os.path.exists(path):
            return {"success": False, "error": "File not found"}

        try:
            stat = os.stat(path)
            return {
                "success": True,
                "path": path,
                "type": "directory" if os.path.isdir(path) else "file",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============== Process Operations ==============

    def execute_command(self, command: str, shell: bool = True, timeout: int = 30) -> Dict:
        """Execute shell command with security checks"""
        safe, reason = self._check_command_safety(command)
        if not safe:
            raise SecurityError(f"Command blocked: {reason}")

        try:
            # Use subprocess with restricted environment
            env = os.environ.copy()
            env['PATH'] = self._get_restricted_path()

            result = subprocess.run(
                command if shell else command.split(),
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace_dir,
                env=env
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_restricted_path(self) -> str:
        """Get restricted PATH environment"""
        if IS_WINDOWS:
            return os.environ.get('PATH', 'C:\\Windows\\System32;C:\\Windows')
        else:
            return '/usr/bin:/bin'

    def get_process_list(self) -> Dict:
        """Get running processes (limited info for security)"""
        try:
            if IS_WINDOWS:
                result = subprocess.run(
                    ['tasklist', '/fo', 'csv', '/nh'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                processes = []
                for line in result.stdout.strip().split('\n'):
                    parts = line.split('","')
                    if len(parts) >= 2:
                        processes.append({
                            "name": parts[0].strip('"'),
                            "pid": parts[1].strip('"')
                        })
            else:
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                processes = []
                for line in result.stdout.strip().split('\n')[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        processes.append({
                            "name": parts[10] if len(parts) > 10 else "unknown",
                            "pid": parts[1]
                        })

            return {"success": True, "processes": processes[:50]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============== Network Operations ==============

    def make_request(self, url: str, method: str = 'GET', data: dict = None,
                     headers: dict = None, timeout: int = 30) -> Dict:
        """Make HTTP request with governance"""
        # Basic URL validation
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return {"success": False, "error": "Only HTTP/HTTPS allowed"}

            # Block private IP ranges
            hostname = parsed.hostname
            if hostname:
                if hostname.startswith(('10.', '192.168.', '172.', '127.', 'localhost')):
                    return {"success": False, "error": "Private network access blocked"}
        except Exception as e:
            return {"success": False, "error": f"URL parsing error: {e}"}

        try:
            req = urllib.request.Request(url, method=method)

            # Add headers
            default_headers = {
                'User-Agent': 'AgentOS/1.0'
            }
            if headers:
                default_headers.update(headers)
            for k, v in default_headers.items():
                req.add_header(k, v)

            # Add body for POST/PUT
            if data and method in ('POST', 'PUT'):
                req.data = json.dumps(data).encode('utf-8')
                req.add_header('Content-Type', 'application/json')

            with urllib.request.urlopen(req, timeout=timeout) as response:
                body = response.read()
                return {
                    "success": True,
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body": body.decode('utf-8', errors='ignore')[:100000]
                }
        except urllib.error.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP {e.code}: {e.reason}",
                "status": e.code
            }
        except urllib.error.URLError as e:
            return {"success": False, "error": f"URL Error: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============== System Operations ==============

    def get_system_info(self) -> Dict:
        """Get system information"""
        try:
            info = {
                "platform": self.platform,
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "workspace_dir": self.workspace_dir,
            }

            # Add platform-specific info
            if IS_WINDOWS:
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                    info["windows_product_name"] = winreg.QueryValueEx(key, "ProductName")[0]
                    winreg.CloseKey(key)
                except:
                    pass

            return {"success": True, **info}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_disk_usage(self) -> Dict:
        """Get disk usage"""
        try:
            if IS_WINDOWS:
                import shutil
                usage = shutil.disk_usage(self.workspace_dir)
                return {
                    "success": True,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100
                }
            else:
                import shutil
                usage = shutil.disk_usage(self.workspace_dir)
                return {
                    "success": True,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============== Path Operations ==============

    def normalize_path(self, path: str) -> str:
        """Normalize path for current platform"""
        return os.path.normpath(os.path.expanduser(path))

    def create_directory(self, path: str) -> Dict:
        """Create directory"""
        safe, reason = self._is_path_safe(path)
        if not safe:
            raise SecurityError(f"Create directory blocked: {reason}")

        try:
            os.makedirs(path, exist_ok=True)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def path_exists(self, path: str) -> bool:
        """Check if path exists"""
        try:
            safe, _ = self._is_path_safe(path)
            return safe and os.path.exists(path)
        except:
            return False

    # ============== File Watching ==============

    def watch_directory(self, path: str, recursive: bool = False) -> Dict:
        """Start watching a directory for changes (returns watcher config)"""
        safe, reason = self._is_path_safe(path)
        if not safe:
            raise SecurityError(f"Watch blocked: {reason}")

        if not os.path.exists(path):
            return {"success": False, "error": "Directory not found"}

        if not os.path.isdir(path):
            return {"success": False, "error": "Path is not a directory"}

        try:
            # Use native OS monitoring (watchdog-like implementation)
            from collections import defaultdict

            watcher_id = f"watch_{uuid.uuid4().hex[:8]}"

            # Store watched paths for later comparison
            if not hasattr(self, '_watched_paths'):
                self._watched_paths = {}

            # Initial scan for comparison
            current_files = {}
            for root, dirs, files in os.walk(path):
                if not recursive and root != path:
                    break
                for f in files:
                    full_path = os.path.join(root, f)
                    try:
                        current_files[full_path] = os.path.getmtime(full_path)
                    except:
                        pass

            self._watched_paths[watcher_id] = {
                "path": path,
                "recursive": recursive,
                "last_scan": current_files,
                "files": current_files
            }

            return {
                "success": True,
                "watcher_id": watcher_id,
                "path": path,
                "file_count": len(current_files)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_for_changes(self, watcher_id: str) -> Dict:
        """Check for file changes in watched directory"""
        if not hasattr(self, '_watched_paths') or watcher_id not in self._watched_paths:
            return {"success": False, "error": "Watcher not found"}

        try:
            watch_info = self._watched_paths[watcher_id]
            path = watch_info["path"]
            recursive = watch_info["recursive"]
            last_files = watch_info.get("files", {})

            # Scan current state
            current_files = {}
            for root, dirs, files in os.walk(path):
                if not recursive and root != path:
                    break
                for f in files:
                    full_path = os.path.join(root, f)
                    try:
                        current_files[full_path] = os.path.getmtime(full_path)
                    except:
                        pass

            # Compare
            changes = {
                "created": [],
                "modified": [],
                "deleted": []
            }

            # Find new and modified files
            for path, mtime in current_files.items():
                if path not in last_files:
                    changes["created"].append(path)
                elif last_files[path] != mtime:
                    changes["modified"].append(path)

            # Find deleted files
            for path in last_files:
                if path not in current_files:
                    changes["deleted"].append(path)

            # Update stored state
            self._watched_paths[watcher_id]["files"] = current_files

            has_changes = any(changes.values())

            return {
                "success": True,
                "watcher_id": watcher_id,
                "has_changes": has_changes,
                "changes": changes,
                "file_count": len(current_files)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_watching(self, watcher_id: str) -> Dict:
        """Stop watching a directory"""
        if not hasattr(self, '_watched_paths') or watcher_id not in self._watched_paths:
            return {"success": False, "error": "Watcher not found"}

        try:
            del self._watched_paths[watcher_id]
            return {"success": True, "watcher_id": watcher_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_watched_directories(self) -> Dict:
        """Get list of currently watched directories"""
        if not hasattr(self, '_watched_paths'):
            return {"success": True, "watchers": []}

        watchers = []
        for wid, info in self._watched_paths.items():
            watchers.append({
                "watcher_id": wid,
                "path": info["path"],
                "recursive": info["recursive"],
                "file_count": len(info.get("files", {}))
            })

        return {"success": True, "watchers": watchers}

    # ============== Batch File Operations ==============

    def copy_file(self, source: str, destination: str) -> Dict:
        """Copy file with security checks"""
        safe_src, reason = self._is_path_safe(source)
        if not safe_src:
            raise SecurityError(f"Copy blocked (source): {reason}")

        safe_dst, reason = self._is_path_safe(destination)
        if not safe_dst:
            raise SecurityError(f"Copy blocked (destination): {reason}")

        if not os.path.exists(source):
            return {"success": False, "error": "Source file not found"}

        try:
            import shutil
            dest_dir = os.path.dirname(destination)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            shutil.copy2(source, destination)
            return {
                "success": True,
                "source": source,
                "destination": destination,
                "size": os.path.getsize(destination)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def move_file(self, source: str, destination: str) -> Dict:
        """Move file with security checks"""
        safe_src, reason = self._is_path_safe(source)
        if not safe_src:
            raise SecurityError(f"Move blocked (source): {reason}")

        safe_dst, reason = self._is_path_safe(destination)
        if not safe_dst:
            raise SecurityError(f"Move blocked (destination): {reason}")

        if not os.path.exists(source):
            return {"success": False, "error": "Source file not found"}

        try:
            import shutil
            dest_dir = os.path.dirname(destination)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            shutil.move(source, destination)
            return {
                "success": True,
                "source": source,
                "destination": destination
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_files(self, directory: str, pattern: str, case_sensitive: bool = False) -> Dict:
        """Search for files matching a pattern"""
        safe, reason = self._is_path_safe(directory)
        if not safe:
            raise SecurityError(f"Search blocked: {reason}")

        if not os.path.exists(directory):
            return {"success": False, "error": "Directory not found"}

        try:
            import fnmatch

            matches = []
            search_pattern = pattern if case_sensitive else pattern.lower()

            for root, dirs, files in os.walk(directory):
                for filename in files:
                    compare_name = filename if case_sensitive else filename.lower()
                    if fnmatch.fnmatch(compare_name, search_pattern):
                        full_path = os.path.join(root, filename)
                        try:
                            stat = os.stat(full_path)
                            matches.append({
                                "name": filename,
                                "path": full_path,
                                "size": stat.st_size,
                                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                            })
                        except:
                            pass

            return {
                "success": True,
                "directory": directory,
                "pattern": pattern,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
os_bridge = OSBridge()
