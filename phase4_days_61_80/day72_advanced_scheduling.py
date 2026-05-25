"""
Day 72: Advanced Scheduling
===========================
Advanced scheduling capabilities for agent task execution.

Key Concepts:
- Cron-like scheduling
- Recurring tasks
- Priority scheduling
- Time-based triggers
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import re
import uuid


class ScheduleType(Enum):
    """Types of schedules"""
    ONCE = "once"
    RECURRING = "recurring"
    CRON = "cron"
    INTERVAL = "interval"


class ScheduleStatus(Enum):
    """Schedule status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"


@dataclass
class Schedule:
    """Task schedule"""
    schedule_id: str
    name: str
    schedule_type: ScheduleType
    task_params: Dict[str, Any]
    cron_expr: str = None
    interval_seconds: int = None
    run_at: datetime = None
    max_runs: int = None
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    run_count: int = 0
    last_run: datetime = None
    next_run: datetime = None
    created_at: datetime = field(default_factory=datetime.now)


class CronParser:
    """Simple cron expression parser"""

    # Cron format: minute hour day month day_of_week
    CRON_PATTERN = re.compile(
        r'^(\d+|\*)(\s+(\d+|\*)){4}$'
    )

    @staticmethod
    def parse(cron_expr: str) -> Dict[str, Any]:
        """Parse cron expression"""
        parts = cron_expr.split()
        return {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "day_of_week": parts[4]
        }

    @staticmethod
    def get_next_run(cron_expr: str, from_time: datetime = None) -> datetime:
        """Calculate next run time from cron expression"""
        from_time = from_time or datetime.now()
        parsed = CronParser.parse(cron_expr)

        # Simple implementation - calculate next minute
        next_time = from_time + timedelta(minutes=1)

        # In a full implementation, this would properly parse
        # minute, hour, day, month, day_of_week patterns
        return next_time


class AdvancedScheduler:
    """
    Advanced Task Scheduler
    ========================

    Schedules and executes tasks with various scheduling strategies.
    """

    def __init__(self):
        self.schedules: Dict[str, Schedule] = {}
        self.handlers: Dict[str, Callable] = {}
        self._running = False
        self._lock = asyncio.Lock()

    def register_handler(self, task_type: str, handler: Callable):
        """Register task handler"""
        self.handlers[task_type] = handler

    def create_one_time(
        self,
        name: str,
        task_type: str,
        task_params: Dict[str, Any],
        run_at: datetime = None
    ) -> Schedule:
        """Create a one-time schedule"""
        schedule = Schedule(
            schedule_id=str(uuid.uuid4()),
            name=name,
            schedule_type=ScheduleType.ONCE,
            task_params={
                "task_type": task_type,
                **task_params
            },
            run_at=run_at or datetime.now() + timedelta(seconds=5),
            max_runs=1
        )

        schedule.next_run = schedule.run_at
        self.schedules[schedule.schedule_id] = schedule
        return schedule

    def create_recurring(
        self,
        name: str,
        task_type: str,
        task_params: Dict[str, Any],
        interval_seconds: int,
        max_runs: int = None
    ) -> Schedule:
        """Create a recurring schedule"""
        schedule = Schedule(
            schedule_id=str(uuid.uuid4()),
            name=name,
            schedule_type=ScheduleType.RECURRING,
            task_params={
                "task_type": task_type,
                **task_params
            },
            interval_seconds=interval_seconds,
            max_runs=max_runs
        )

        schedule.next_run = datetime.now() + timedelta(seconds=interval_seconds)
        self.schedules[schedule.schedule_id] = schedule
        return schedule

    def create_cron(
        self,
        name: str,
        task_type: str,
        task_params: Dict[str, Any],
        cron_expr: str,
        max_runs: int = None
    ) -> Schedule:
        """Create a cron-based schedule"""
        schedule = Schedule(
            schedule_id=str(uuid.uuid4()),
            name=name,
            schedule_type=ScheduleType.CRON,
            task_params={
                "task_type": task_type,
                **task_params
            },
            cron_expr=cron_expr,
            max_runs=max_runs
        )

        schedule.next_run = CronParser.get_next_run(cron_expr)
        self.schedules[schedule.schedule_id] = schedule
        return schedule

    async def start(self):
        """Start the scheduler"""
        self._running = True
        asyncio.create_task(self._run_scheduler())

    async def stop(self):
        """Stop the scheduler"""
        self._running = False

    async def _run_scheduler(self):
        """Main scheduler loop"""
        while self._running:
            now = datetime.now()

            async with self._lock:
                for schedule in self.schedules.values():
                    if schedule.status != ScheduleStatus.ACTIVE:
                        continue

                    # Check if it's time to run
                    if schedule.next_run and now >= schedule.next_run:
                        await self._execute_schedule(schedule)

            await asyncio.sleep(1)

    async def _execute_schedule(self, schedule: Schedule):
        """Execute a scheduled task"""
        task_type = schedule.task_params.get("task_type")
        handler = self.handlers.get(task_type)

        if handler:
            try:
                # Execute task
                task_params = {k: v for k, v in schedule.task_params.items()
                              if k != "task_type"}

                if asyncio.iscoroutinefunction(handler):
                    await handler(task_params)
                else:
                    handler(task_params)

                schedule.run_count += 1
                schedule.last_run = datetime.now()

            except Exception as e:
                print(f"Schedule execution error: {e}")

        # Calculate next run
        if schedule.schedule_type == ScheduleType.RECURRING:
            schedule.next_run = datetime.now() + timedelta(
                seconds=schedule.interval_seconds
            )
        elif schedule.schedule_type == ScheduleType.CRON and schedule.cron_expr:
            schedule.next_run = CronParser.get_next_run(schedule.cron_expr)
        elif schedule.schedule_type == ScheduleType.ONCE:
            schedule.next_run = None
            schedule.status = ScheduleStatus.COMPLETED

        # Check max runs
        if schedule.max_runs and schedule.run_count >= schedule.max_runs:
            schedule.status = ScheduleStatus.COMPLETED
            schedule.next_run = None

    def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a schedule"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id].status = ScheduleStatus.PAUSED
            return True
        return False

    def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a schedule"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id].status = ScheduleStatus.ACTIVE
            return True
        return False

    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get schedule by ID"""
        return self.schedules.get(schedule_id)

    def list_schedules(self) -> List[Dict[str, Any]]:
        """List all schedules"""
        return [
            {
                "schedule_id": s.schedule_id,
                "name": s.name,
                "type": s.schedule_type.value,
                "status": s.status.value,
                "next_run": s.next_run.isoformat() if s.next_run else None,
                "run_count": s.run_count,
                "max_runs": s.max_runs
            }
            for s in self.schedules.values()
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        by_status = {}
        by_type = {}

        for s in self.schedules.values():
            status = s.status.value
            stype = s.schedule_type.value

            by_status[status] = by_status.get(status, 0) + 1
            by_type[stype] = by_type.get(stype, 0) + 1

        return {
            "total_schedules": len(self.schedules),
            "by_status": by_status,
            "by_type": by_type,
            "running": self._running
        }


# Demo
async def main():
    print("=" * 60)
    print("Day 72: Advanced Scheduling")
    print("=" * 60)

    scheduler = AdvancedScheduler()

    # Register handlers
    async def daily_report(params):
        print(f"  Running daily report: {params}")

    def cleanup_task(params):
        print(f"  Running cleanup: {params}")

    def health_check(params):
        print(f"  Health check: {params}")

    scheduler.register_handler("daily_report", daily_report)
    scheduler.register_handler("cleanup", cleanup_task)
    scheduler.register_handler("health_check", health_check)

    # Create schedules
    print("\nCreating schedules...")

    scheduler.create_one_time(
        name="Initial Setup",
        task_type="daily_report",
        task_params={"type": "initial"}
    )

    scheduler.create_recurring(
        name="Data Cleanup",
        task_type="cleanup",
        task_params={"older_than_days": 30},
        interval_seconds=10,
        max_runs=3
    )

    scheduler.create_cron(
        name="Health Check",
        task_type="health_check",
        task_params={"checks": ["memory", "disk", "cpu"]},
        cron_expr="* * * * *",  # Every minute for demo
        max_runs=5
    )

    # List schedules
    print("\nSchedules:")
    for s in scheduler.list_schedules():
        print(f"  - {s['name']} ({s['type']})")
        print(f"    Status: {s['status']}, Next: {s['next_run']}")

    # Start scheduler
    print("\nStarting scheduler...")
    await scheduler.start()

    # Let it run for a bit
    await asyncio.sleep(15)

    # Stop scheduler
    await scheduler.stop()

    # Show results
    print("\nFinal status:")
    for s in scheduler.list_schedules():
        print(f"  - {s['name']}: {s['run_count']} runs")

    stats = scheduler.get_stats()
    print(f"\nScheduler stats:")
    print(f"  Total: {stats['total_schedules']}")
    print(f"  By status: {stats['by_status']}")


if __name__ == "__main__":
    asyncio.run(main())