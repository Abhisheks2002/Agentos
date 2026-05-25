"""
AgentOS - Database Layer
SQLite-based persistence for organizations, agents, workflows, and audit logs
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agentos.db')


class Database:
    """SQLite database for AgentOS persistence"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.conn = None
        self._init_db()

    def _get_connection(self):
        """Get database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def _init_db(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Organizations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                tier TEXT NOT NULL,
                created_at TEXT NOT NULL,
                config TEXT
            )
        ''')

        # Agents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                name TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'idle',
                permissions TEXT,
                tasks_completed INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_activity TEXT,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            )
        ''')

        # Workflows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                nodes TEXT,
                status TEXT DEFAULT 'draft',
                trigger_type TEXT,
                runs INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_run TEXT,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            )
        ''')

        # Audit logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id TEXT NOT NULL,
                agent_id TEXT,
                action TEXT NOT NULL,
                details TEXT,
                status TEXT NOT NULL,
                reason TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            )
        ''')

        # Governance rules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS governance_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id TEXT NOT NULL,
                name TEXT NOT NULL,
                permission TEXT NOT NULL,
                action TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            )
        ''')

        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                task_type TEXT NOT NULL,
                payload TEXT,
                priority INTEGER DEFAULT 1,
                state TEXT DEFAULT 'queued',
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                result TEXT,
                error TEXT,
                depends_on TEXT,
                timeout INTEGER DEFAULT 300
            )
        ''')

        conn.commit()

    # ============== Organizations ==============

    def save_organization(self, org: Dict) -> bool:
        """Save organization"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO organizations (id, name, tier, created_at, config)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                org['id'],
                org['name'],
                org['tier'],
                org.get('created_at', datetime.now().isoformat()),
                json.dumps(org.get('config', {}))
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving organization: {e}")
            return False

    def get_organization(self, org_id: str) -> Optional[Dict]:
        """Get organization by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM organizations WHERE id = ?', (org_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"Error getting organization: {e}")
            return None

    def get_all_organizations(self) -> List[Dict]:
        """Get all organizations"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM organizations ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting organizations: {e}")
            return []

    def delete_organization(self, org_id: str) -> bool:
        """Delete organization"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM organizations WHERE id = ?', (org_id,))
            # Cascade delete
            cursor.execute('DELETE FROM agents WHERE org_id = ?', (org_id,))
            cursor.execute('DELETE FROM workflows WHERE org_id = ?', (org_id,))
            cursor.execute('DELETE FROM audit_logs WHERE org_id = ?', (org_id,))
            cursor.execute('DELETE FROM governance_rules WHERE org_id = ?', (org_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting organization: {e}")
            return False

    # ============== Agents ==============

    def save_agent(self, agent: Dict) -> bool:
        """Save agent"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO agents
                (id, org_id, name, agent_type, description, status, permissions,
                 tasks_completed, errors, created_at, last_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent['id'],
                agent['org_id'],
                agent['name'],
                agent.get('type', 'unknown'),
                agent.get('description', ''),
                agent.get('status', 'idle'),
                json.dumps(agent.get('permissions', [])),
                agent.get('tasks_completed', 0),
                agent.get('errors', 0),
                agent.get('created_at', datetime.now().isoformat()),
                agent.get('last_activity')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving agent: {e}")
            return False

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"Error getting agent: {e}")
            return None

    def get_agents_by_org(self, org_id: str) -> List[Dict]:
        """Get all agents for organization"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM agents WHERE org_id = ? ORDER BY created_at DESC', (org_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting agents: {e}")
            return []

    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """Update agent status"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE agents SET status = ?, last_activity = ?
                WHERE id = ?
            ''', (status, datetime.now().isoformat(), agent_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating agent status: {e}")
            return False

    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM agents WHERE id = ?', (agent_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting agent: {e}")
            return False

    # ============== Workflows ==============

    def save_workflow(self, workflow: Dict) -> bool:
        """Save workflow"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO workflows
                (id, org_id, name, description, nodes, status, trigger_type,
                 runs, created_at, last_run)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                workflow['id'],
                workflow['org_id'],
                workflow['name'],
                workflow.get('description', ''),
                json.dumps(workflow.get('nodes', [])),
                workflow.get('status', 'draft'),
                workflow.get('trigger'),
                workflow.get('runs', 0),
                workflow.get('created_at', datetime.now().isoformat()),
                workflow.get('last_run')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving workflow: {e}")
            return False

    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM workflows WHERE id = ?', (workflow_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"Error getting workflow: {e}")
            return None

    def get_workflows_by_org(self, org_id: str) -> List[Dict]:
        """Get all workflows for organization"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM workflows WHERE org_id = ? ORDER BY created_at DESC', (org_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting workflows: {e}")
            return []

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM workflows WHERE id = ?', (workflow_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting workflow: {e}")
            return False

    # ============== Audit Logs ==============

    def save_audit_log(self, log: Dict) -> bool:
        """Save audit log entry"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_logs
                (org_id, agent_id, action, details, status, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                log.get('org_id'),
                log.get('agent_id'),
                log.get('action'),
                log.get('details'),
                log.get('status'),
                log.get('reason', ''),
                log.get('timestamp', datetime.now().isoformat())
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving audit log: {e}")
            return False

    def get_audit_logs(self, org_id: str, limit: int = 100,
                       status: str = None, agent_id: str = None) -> List[Dict]:
        """Get audit logs for organization"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = 'SELECT * FROM audit_logs WHERE org_id = ?'
            params = [org_id]

            if status:
                query += ' AND status = ?'
                params.append(status)
            if agent_id:
                query += ' AND agent_id = ?'
                params.append(agent_id)

            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting audit logs: {e}")
            return []

    def get_audit_stats(self, org_id: str) -> Dict:
        """Get audit statistics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM audit_logs
                WHERE org_id = ?
                GROUP BY status
            ''', (org_id,))

            stats = {'allowed': 0, 'blocked': 0, 'warning': 0}
            for row in cursor.fetchall():
                stats[row['status']] = row['count']

            return stats
        except Exception as e:
            print(f"Error getting audit stats: {e}")
            return stats

    # ============== Settings ==============

    def save_setting(self, key: str, value: Any) -> bool:
        """Save setting"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            ''', (key, json.dumps(value)))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving setting: {e}")
            return False

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row['value'])
            return default
        except Exception as e:
            print(f"Error getting setting: {e}")
            return default

    # ============== Utilities ==============

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    # ============== Tasks ==============

    def save_task(self, task: Dict) -> bool:
        """Save task"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO tasks
                (task_id, agent_id, task_type, payload, priority, state,
                 created_at, started_at, completed_at, retry_count,
                 max_retries, result, error, depends_on, timeout)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.get('task_id'),
                task.get('agent_id'),
                task.get('task_type'),
                json.dumps(task.get('payload', {})),
                task.get('priority', 1),
                task.get('state', 'queued'),
                task.get('created_at'),
                task.get('started_at'),
                task.get('completed_at'),
                task.get('retry_count', 0),
                task.get('max_retries', 3),
                json.dumps(task.get('result')) if task.get('result') else None,
                task.get('error'),
                json.dumps(task.get('depends_on', [])),
                task.get('timeout', 300)
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving task: {e}")
            return False

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"Error getting task: {e}")
            return None

    def get_tasks_by_agent(self, agent_id: str) -> List[Dict]:
        """Get all tasks for agent"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM tasks WHERE agent_id = ?
                ORDER BY priority ASC, created_at ASC
            ''', (agent_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting tasks by agent: {e}")
            return []

    def get_pending_tasks(self) -> List[Dict]:
        """Get pending/retry tasks"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM tasks
                WHERE state IN ('queued', 'retry')
                ORDER BY priority ASC, created_at ASC
            ''')
            results = []
            for row in cursor.fetchall():
                task_dict = dict(row)
                # Parse JSON fields
                if task_dict.get('payload'):
                    task_dict['payload'] = json.loads(task_dict['payload'])
                if task_dict.get('result'):
                    task_dict['result'] = json.loads(task_dict['result'])
                if task_dict.get('depends_on'):
                    task_dict['depends_on'] = json.loads(task_dict['depends_on'])
                results.append(task_dict)
            return results
        except Exception as e:
            print(f"Error getting pending tasks: {e}")
            return []

    def update_task_state(self, task_id: str, state: str) -> bool:
        """Update task state"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            if state == 'processing':
                cursor.execute('''
                    UPDATE tasks SET state = ?, started_at = ?
                    WHERE task_id = ?
                ''', (state, now, task_id))
            elif state == 'completed':
                cursor.execute('''
                    UPDATE tasks SET state = ?, completed_at = ?
                    WHERE task_id = ?
                ''', (state, now, task_id))
            elif state == 'failed':
                cursor.execute('''
                    UPDATE tasks SET state = ?, completed_at = ?
                    WHERE task_id = ?
                ''', (state, now, task_id))
            else:
                cursor.execute('UPDATE tasks SET state = ? WHERE task_id = ?', (state, task_id))

            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating task state: {e}")
            return False

    def update_task_result(self, task_id: str, result: Dict, error: str = None) -> bool:
        """Update task result"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tasks SET result = ?, error = ?, completed_at = ?
                WHERE task_id = ?
            ''', (
                json.dumps(result) if result else None,
                error,
                datetime.now().isoformat(),
                task_id
            ))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating task result: {e}")
            return False

    def increment_task_retry(self, task_id: str) -> bool:
        """Increment task retry count"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tasks SET retry_count = retry_count + 1
                WHERE task_id = ?
            ''', (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error incrementing retry: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """Delete task"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE task_id = ?', (task_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False

    def get_task_stats(self, agent_id: str = None) -> Dict:
        """Get task statistics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = 'SELECT state, COUNT(*) as count FROM tasks'
            params = []
            if agent_id:
                query += ' WHERE agent_id = ?'
                params.append(agent_id)
            query += ' GROUP BY state'

            cursor.execute(query, params)

            stats = {
                'queued': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'retry': 0,
                'cancelled': 0
            }

            for row in cursor.fetchall():
                state = row['state']
                if state in stats:
                    stats[state] = row['count']

            return stats
        except Exception as e:
            print(f"Error getting task stats: {e}")
            return {'queued': 0, 'processing': 0, 'completed': 0, 'failed': 0, 'retry': 0, 'cancelled': 0}


# Singleton instance
db = Database()
