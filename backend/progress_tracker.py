"""
Progress Tracker Module
Provides thread-safe global state management for tracking generation progress
without constantly writing to Supabase.
"""
import threading
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RunProgress:
    """Represents the progress state of a generation run."""
    run_id: str
    progress: int  # 0-100
    is_complete: bool
    error: Optional[str] = None
    started_at: datetime = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.utcnow()


class ProgressTracker:
    """
    Thread-safe singleton for tracking progress of generation runs.
    Stores progress in memory to avoid excessive database writes.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._progress_data: Dict[str, RunProgress] = {}
        self._data_lock = threading.Lock()

    def create_run(self, run_id: str) -> None:
        """Initialize a new run with 0% progress."""
        with self._data_lock:
            self._progress_data[run_id] = RunProgress(
                run_id=run_id,
                progress=0,
                is_complete=False
            )

    def update_progress(self, run_id: str, progress: int) -> None:
        """Update the progress for a run (0-100)."""
        with self._data_lock:
            if run_id in self._progress_data:
                self._progress_data[run_id].progress = min(100, max(0, progress))

    def mark_complete(self, run_id: str) -> None:
        """Mark a run as complete."""
        with self._data_lock:
            if run_id in self._progress_data:
                self._progress_data[run_id].is_complete = True
                self._progress_data[run_id].progress = 100
                self._progress_data[run_id].completed_at = datetime.utcnow()

    def mark_error(self, run_id: str, error_message: str) -> None:
        """Mark a run as failed with an error message."""
        with self._data_lock:
            if run_id in self._progress_data:
                self._progress_data[run_id].error = error_message
                self._progress_data[run_id].is_complete = True
                self._progress_data[run_id].completed_at = datetime.utcnow()

    def get_progress(self, run_id: str) -> Optional[RunProgress]:
        """Get the current progress for a run."""
        with self._data_lock:
            return self._progress_data.get(run_id)

    def get_multiple_progress(self, run_ids: list) -> Dict[str, Optional[RunProgress]]:
        """Get progress for multiple runs at once."""
        with self._data_lock:
            return {run_id: self._progress_data.get(run_id) for run_id in run_ids}

    def cleanup_run(self, run_id: str) -> None:
        """Remove a run from tracking (call after client has fetched results)."""
        with self._data_lock:
            if run_id in self._progress_data:
                del self._progress_data[run_id]

    def cleanup_old_runs(self, max_age_hours: int = 24) -> None:
        """Clean up runs older than specified hours."""
        with self._data_lock:
            now = datetime.utcnow()
            to_remove = []
            for run_id, progress in self._progress_data.items():
                age_hours = (now - progress.started_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    to_remove.append(run_id)

            for run_id in to_remove:
                del self._progress_data[run_id]


# Global singleton instance
progress_tracker = ProgressTracker()
