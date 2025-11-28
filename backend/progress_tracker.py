"""
Progress Tracker Module
Provides progress tracking using Supabase database for multi-worker compatibility.
Works correctly with Gunicorn's multiple worker processes.

Uses the 'intermediate_outputs' JSON column to store progress since we can't add new columns.
Progress is stored as: intermediate_outputs.progress_percent
"""
import threading
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from db_utils import supabase


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
    Progress tracker that stores progress in Supabase database.
    This allows multiple Gunicorn workers to share progress state.
    
    Uses intermediate_outputs JSON column to store progress_percent.
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

    def create_run(self, run_id: str) -> None:
        """
        Initialize a new run with 0% progress.
        Sets intermediate_outputs to include progress_percent.
        """
        try:
            supabase.table('runs').update({
                'intermediate_outputs': {'progress_percent': 0}
            }).eq('id', int(run_id)).execute()
        except Exception as e:
            print(f"Error creating run progress: {e}")

    def update_progress(self, run_id: str, progress: int) -> None:
        """Update the progress for a run (0-100)."""
        try:
            clamped_progress = min(100, max(0, progress))
            
            # Get current intermediate_outputs to preserve other data
            result = supabase.table('runs').select('intermediate_outputs').eq('id', int(run_id)).execute()
            
            current_outputs = {}
            if result.data and result.data[0].get('intermediate_outputs'):
                current_outputs = result.data[0]['intermediate_outputs']
            
            # Update progress_percent
            current_outputs['progress_percent'] = clamped_progress
            
            supabase.table('runs').update({
                'intermediate_outputs': current_outputs
            }).eq('id', int(run_id)).execute()
        except Exception as e:
            print(f"Error updating progress: {e}")

    def mark_complete(self, run_id: str) -> None:
        """Mark a run as complete."""
        try:
            # Get current intermediate_outputs to preserve other data
            result = supabase.table('runs').select('intermediate_outputs').eq('id', int(run_id)).execute()
            
            current_outputs = {}
            if result.data and result.data[0].get('intermediate_outputs'):
                current_outputs = result.data[0]['intermediate_outputs']
            
            current_outputs['progress_percent'] = 100
            
            supabase.table('runs').update({
                'intermediate_outputs': current_outputs,
                'status': 'completed'
            }).eq('id', int(run_id)).execute()
        except Exception as e:
            print(f"Error marking complete: {e}")

    def mark_error(self, run_id: str, error_message: str) -> None:
        """Mark a run as failed with an error message."""
        try:
            supabase.table('runs').update({
                'error': error_message,
                'status': 'failed'
            }).eq('id', int(run_id)).execute()
        except Exception as e:
            print(f"Error marking error: {e}")

    def get_progress(self, run_id: str) -> Optional[RunProgress]:
        """Get the current progress for a run from the database."""
        try:
            result = supabase.table('runs').select('id,intermediate_outputs,status,error').eq('id', int(run_id)).execute()
            
            if not result.data or len(result.data) == 0:
                return None
            
            row = result.data[0]
            intermediate_outputs = row.get('intermediate_outputs') or {}
            progress = intermediate_outputs.get('progress_percent', 0) or 0
            
            return RunProgress(
                run_id=str(row['id']),
                progress=progress,
                is_complete=row.get('status') in ('completed', 'failed'),
                error=row.get('error')
            )
        except Exception as e:
            print(f"Error getting progress: {e}")
            return None

    def get_multiple_progress(self, run_ids: list) -> Dict[str, Optional[RunProgress]]:
        """Get progress for multiple runs at once from the database."""
        try:
            # Convert string IDs to integers for the query
            int_ids = [int(rid) for rid in run_ids]
            
            result = supabase.table('runs').select('id,intermediate_outputs,status,error').in_('id', int_ids).execute()
            
            # Build a map of results
            results_map = {}
            for row in result.data:
                run_id_str = str(row['id'])
                intermediate_outputs = row.get('intermediate_outputs') or {}
                progress = intermediate_outputs.get('progress_percent', 0) or 0
                
                results_map[run_id_str] = RunProgress(
                    run_id=run_id_str,
                    progress=progress,
                    is_complete=row.get('status') in ('completed', 'failed'),
                    error=row.get('error')
                )
            
            # Return results for all requested IDs (None if not found)
            return {run_id: results_map.get(run_id) for run_id in run_ids}
            
        except Exception as e:
            print(f"Error getting multiple progress: {e}")
            return {run_id: None for run_id in run_ids}

    def cleanup_run(self, run_id: str) -> None:
        """No-op for database-backed tracker (data persists in DB)."""
        pass

    def cleanup_old_runs(self, max_age_hours: int = 24) -> None:
        """No-op for database-backed tracker (use DB cleanup instead)."""
        pass


# Global singleton instance
progress_tracker = ProgressTracker()
