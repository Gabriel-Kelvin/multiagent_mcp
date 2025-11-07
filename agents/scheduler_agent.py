from typing import Callable, Any, Dict, List, Optional
import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.logging_utils import JsonSqlLogger


class SchedulerService:
    """Singleton scheduler service for managing scheduled jobs"""
    _instance: Optional[BackgroundScheduler] = None
    _jobs_db: Dict[str, Dict[str, Any]] = {}  # In-memory job store
    
    @classmethod
    def get_scheduler(cls, timezone: str = "UTC") -> BackgroundScheduler:
        if cls._instance is None:
            cls._instance = BackgroundScheduler(timezone=timezone)
            cls._instance.start()
        return cls._instance
    
    @classmethod
    def add_job(cls, job_id: str, question: str, frequency: str, time_str: str, 
                overrides: Dict[str, Any], func: Callable, logger: Optional[JsonSqlLogger] = None) -> str:
        """Add a scheduled job with cron trigger"""
        scheduler = cls.get_scheduler()
        
        # Parse time (HH:MM format)
        hour, minute = 0, 0
        if ":" in time_str:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])
        
        # Build cron trigger based on frequency
        if frequency == "daily":
            trigger = CronTrigger(hour=hour, minute=minute)
        elif frequency == "weekly":
            trigger = CronTrigger(day_of_week=0, hour=hour, minute=minute)  # Monday
        elif frequency == "monthly":
            trigger = CronTrigger(day=1, hour=hour, minute=minute)  # 1st of month
        else:
            trigger = CronTrigger(hour=hour, minute=minute)  # Default: daily
        
        # Add job to scheduler
        job = scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            kwargs={"question": question, "overrides": overrides, "user_id": "scheduler"},
            replace_existing=True
        )
        
        # Store job metadata
        cls._jobs_db[job_id] = {
            "id": job_id,
            "question": question,
            "frequency": frequency,
            "time": time_str,
            "overrides": overrides,
            "created_at": datetime.utcnow().isoformat(),
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        }
        
        if logger:
            logger.info("scheduler", "scheduler", "job_added", {"job_id": job_id, "frequency": frequency, "time": time_str})
        
        return job_id
    
    @classmethod
    def remove_job(cls, job_id: str) -> bool:
        """Remove a scheduled job"""
        scheduler = cls.get_scheduler()
        try:
            scheduler.remove_job(job_id)
            if job_id in cls._jobs_db:
                del cls._jobs_db[job_id]
            return True
        except Exception:
            return False
    
    @classmethod
    def list_jobs(cls) -> List[Dict[str, Any]]:
        """List all scheduled jobs"""
        return list(cls._jobs_db.values())
    
    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID"""
        return cls._jobs_db.get(job_id)


def build_cron_dict(frequency: str, time_str: str) -> Dict[str, Any]:
    """Build cron dict for APScheduler from frequency and time"""
    hour, minute = 0, 0
    if ":" in time_str:
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
    
    if frequency == "daily":
        return {"hour": hour, "minute": minute}
    elif frequency == "weekly":
        return {"day_of_week": "mon", "hour": hour, "minute": minute}
    elif frequency == "monthly":
        return {"day": 1, "hour": hour, "minute": minute}
    else:
        return {"hour": hour, "minute": minute}
