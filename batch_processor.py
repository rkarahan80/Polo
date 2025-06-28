import asyncio
import json
import os
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading

class BatchStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BatchJob:
    id: str
    prompt: str
    model: str
    settings: Dict[str, Any]
    status: BatchStatus = BatchStatus.PENDING
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    progress: float = 0.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

class BatchProcessor:
    """
    Advanced batch processing system for handling multiple video generation requests.
    Supports queue management, progress tracking, and concurrent processing.
    """
    
    def __init__(self, max_concurrent_jobs: int = 2, output_dir: str = "batch_outputs"):
        """
        Initialize the batch processor.
        
        Args:
            max_concurrent_jobs: Maximum number of jobs to process concurrently
            output_dir: Directory to save batch outputs
        """
        self.max_concurrent_jobs = max_concurrent_jobs
        self.output_dir = output_dir
        self.jobs: Dict[str, BatchJob] = {}
        self.queue: List[str] = []  # Job IDs in processing order
        self.active_jobs: Dict[str, threading.Thread] = {}
        self.is_processing = False
        self.progress_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Load existing jobs if any
        self.load_jobs()
    
    def add_progress_callback(self, callback: Callable[[str, float, str], None]):
        """Add a callback for progress updates."""
        self.progress_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable[[str, BatchStatus, Optional[str]], None]):
        """Add a callback for job completion."""
        self.completion_callbacks.append(callback)
    
    def _notify_progress(self, job_id: str, progress: float, message: str):
        """Notify all progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(job_id, progress, message)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    def _notify_completion(self, job_id: str, status: BatchStatus, output_path: Optional[str] = None):
        """Notify all completion callbacks."""
        for callback in self.completion_callbacks:
            try:
                callback(job_id, status, output_path)
            except Exception as e:
                print(f"Error in completion callback: {e}")
    
    def add_job(self, prompt: str, model: str, settings: Dict[str, Any]) -> str:
        """
        Add a new job to the batch queue.
        
        Args:
            prompt: Text prompt for video generation
            model: AI model to use
            settings: Generation settings
        
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        job = BatchJob(
            id=job_id,
            prompt=prompt,
            model=model,
            settings=settings
        )
        
        self.jobs[job_id] = job
        self.queue.append(job_id)
        
        self.save_jobs()
        print(f"Added job {job_id} to batch queue")
        
        # Start processing if not already running
        if not self.is_processing:
            self.start_processing()
        
        return job_id
    
    def add_multiple_jobs(self, job_data: List[Dict[str, Any]]) -> List[str]:
        """
        Add multiple jobs at once.
        
        Args:
            job_data: List of job dictionaries with 'prompt', 'model', and 'settings'
        
        Returns:
            List of job IDs
        """
        job_ids = []
        for data in job_data:
            job_id = self.add_job(
                prompt=data['prompt'],
                model=data['model'],
                settings=data.get('settings', {})
            )
            job_ids.append(job_id)
        
        return job_ids
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[BatchJob]:
        """Get all jobs."""
        return list(self.jobs.values())
    
    def get_jobs_by_status(self, status: BatchStatus) -> List[BatchJob]:
        """Get jobs filtered by status."""
        return [job for job in self.jobs.values() if job.status == status]
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: ID of the job to cancel
        
        Returns:
            True if job was cancelled, False if not found or already completed
        """
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]:
            return False
        
        job.status = BatchStatus.CANCELLED
        job.completed_at = time.time()
        
        # Remove from queue if pending
        if job_id in self.queue:
            self.queue.remove(job_id)
        
        # Stop active job if processing
        if job_id in self.active_jobs:
            # Note: This is a simplified cancellation. In a real implementation,
            # you'd need to properly interrupt the generation process
            thread = self.active_jobs[job_id]
            # thread.stop() # Not directly possible with threading
            del self.active_jobs[job_id]
        
        self.save_jobs()
        self._notify_completion(job_id, BatchStatus.CANCELLED)
        
        print(f"Cancelled job {job_id}")
        return True
    
    def clear_completed_jobs(self):
        """Remove all completed, failed, and cancelled jobs."""
        to_remove = []
        for job_id, job in self.jobs.items():
            if job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]:
                to_remove.append(job_id)
        
        for job_id in to_remove:
            del self.jobs[job_id]
        
        self.save_jobs()
        print(f"Cleared {len(to_remove)} completed jobs")
    
    def start_processing(self):
        """Start the batch processing loop."""
        if self.is_processing:
            return
        
        self.is_processing = True
        processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        processing_thread.start()
        print("Started batch processing")
    
    def stop_processing(self):
        """Stop batch processing."""
        self.is_processing = False
        print("Stopped batch processing")
    
    def _processing_loop(self):
        """Main processing loop."""
        while self.is_processing:
            # Check if we can start new jobs
            if len(self.active_jobs) < self.max_concurrent_jobs and self.queue:
                job_id = self.queue.pop(0)
                job = self.jobs.get(job_id)
                
                if job and job.status == BatchStatus.PENDING:
                    # Start processing the job
                    job_thread = threading.Thread(
                        target=self._process_job,
                        args=(job_id,),
                        daemon=True
                    )
                    job_thread.start()
                    self.active_jobs[job_id] = job_thread
            
            # Clean up completed threads
            completed_threads = []
            for job_id, thread in self.active_jobs.items():
                if not thread.is_alive():
                    completed_threads.append(job_id)
            
            for job_id in completed_threads:
                del self.active_jobs[job_id]
            
            # Check if we should continue processing
            if not self.queue and not self.active_jobs:
                self.is_processing = False
                break
            
            time.sleep(1)  # Check every second
    
    def _process_job(self, job_id: str):
        """
        Process a single job.
        
        Args:
            job_id: ID of the job to process
        """
        job = self.jobs.get(job_id)
        if not job:
            return
        
        try:
            # Update job status
            job.status = BatchStatus.PROCESSING
            job.started_at = time.time()
            job.progress = 0.0
            
            self._notify_progress(job_id, 0.0, "Starting generation...")
            
            # Simulate video generation process
            # In a real implementation, this would call the actual generation functions
            self._simulate_generation(job)
            
            # Mark as completed
            job.status = BatchStatus.COMPLETED
            job.completed_at = time.time()
            job.progress = 100.0
            job.output_path = os.path.join(self.output_dir, f"{job_id}.mp4")
            
            self._notify_progress(job_id, 100.0, "Generation completed!")
            self._notify_completion(job_id, BatchStatus.COMPLETED, job.output_path)
            
        except Exception as e:
            # Mark as failed
            job.status = BatchStatus.FAILED
            job.completed_at = time.time()
            job.error_message = str(e)
            
            self._notify_completion(job_id, BatchStatus.FAILED)
            print(f"Job {job_id} failed: {e}")
        
        finally:
            self.save_jobs()
    
    def _simulate_generation(self, job: BatchJob):
        """
        Simulate the video generation process with progress updates.
        
        Args:
            job: The job being processed
        """
        steps = [
            (10, "Initializing model..."),
            (25, "Processing prompt..."),
            (50, "Generating frames..."),
            (75, "Rendering video..."),
            (90, "Post-processing..."),
            (100, "Finalizing output...")
        ]
        
        for progress, message in steps:
            if job.status == BatchStatus.CANCELLED:
                raise Exception("Job was cancelled")
            
            job.progress = progress
            self._notify_progress(job.id, progress, message)
            
            # Simulate processing time
            time.sleep(2 + (progress * 0.05))  # Variable delay based on step
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.
        
        Returns:
            Dictionary with queue information
        """
        pending_jobs = len(self.get_jobs_by_status(BatchStatus.PENDING))
        processing_jobs = len(self.get_jobs_by_status(BatchStatus.PROCESSING))
        completed_jobs = len(self.get_jobs_by_status(BatchStatus.COMPLETED))
        failed_jobs = len(self.get_jobs_by_status(BatchStatus.FAILED))
        
        return {
            'total_jobs': len(self.jobs),
            'pending': pending_jobs,
            'processing': processing_jobs,
            'completed': completed_jobs,
            'failed': failed_jobs,
            'queue_length': len(self.queue),
            'active_jobs': len(self.active_jobs),
            'is_processing': self.is_processing
        }
    
    def get_estimated_completion_time(self) -> Optional[float]:
        """
        Estimate completion time for all pending jobs.
        
        Returns:
            Estimated completion time in seconds, or None if no data
        """
        completed_jobs = self.get_jobs_by_status(BatchStatus.COMPLETED)
        if not completed_jobs:
            return None
        
        # Calculate average processing time
        total_time = 0
        for job in completed_jobs:
            if job.started_at and job.completed_at:
                total_time += job.completed_at - job.started_at
        
        avg_time = total_time / len(completed_jobs)
        
        # Estimate for remaining jobs
        pending_count = len(self.get_jobs_by_status(BatchStatus.PENDING))
        processing_count = len(self.get_jobs_by_status(BatchStatus.PROCESSING))
        
        # Account for concurrent processing
        remaining_time = (pending_count + processing_count) * avg_time / self.max_concurrent_jobs
        
        return remaining_time
    
    def save_jobs(self):
        """Save jobs to disk."""
        try:
            jobs_data = {}
            for job_id, job in self.jobs.items():
                job_dict = asdict(job)
                job_dict['status'] = job.status.value  # Convert enum to string
                jobs_data[job_id] = job_dict
            
            with open(os.path.join(self.output_dir, 'jobs.json'), 'w') as f:
                json.dump({
                    'jobs': jobs_data,
                    'queue': self.queue
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving jobs: {e}")
    
    def load_jobs(self):
        """Load jobs from disk."""
        try:
            jobs_file = os.path.join(self.output_dir, 'jobs.json')
            if os.path.exists(jobs_file):
                with open(jobs_file, 'r') as f:
                    data = json.load(f)
                
                # Load jobs
                for job_id, job_data in data.get('jobs', {}).items():
                    job_data['status'] = BatchStatus(job_data['status'])  # Convert string to enum
                    job = BatchJob(**job_data)
                    self.jobs[job_id] = job
                
                # Load queue (only pending jobs)
                self.queue = [job_id for job_id in data.get('queue', []) 
                             if job_id in self.jobs and self.jobs[job_id].status == BatchStatus.PENDING]
                
                print(f"Loaded {len(self.jobs)} jobs from disk")
        except Exception as e:
            print(f"Error loading jobs: {e}")
    
    def export_results(self, output_file: str = None) -> str:
        """
        Export batch results to a JSON file.
        
        Args:
            output_file: Path to output file (optional)
        
        Returns:
            Path to the exported file
        """
        if output_file is None:
            timestamp = int(time.time())
            output_file = os.path.join(self.output_dir, f'batch_results_{timestamp}.json')
        
        results = {
            'export_time': time.time(),
            'summary': self.get_queue_status(),
            'jobs': []
        }
        
        for job in self.jobs.values():
            job_result = asdict(job)
            job_result['status'] = job.status.value
            results['jobs'].append(job_result)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Exported batch results to {output_file}")
        return output_file

# Example usage and testing
if __name__ == "__main__":
    # Create batch processor
    processor = BatchProcessor(max_concurrent_jobs=2)
    
    # Add progress callback
    def progress_callback(job_id, progress, message):
        print(f"Job {job_id[:8]}: {progress:.1f}% - {message}")
    
    def completion_callback(job_id, status, output_path):
        print(f"Job {job_id[:8]} completed with status: {status.value}")
    
    processor.add_progress_callback(progress_callback)
    processor.add_completion_callback(completion_callback)
    
    # Add some test jobs
    test_jobs = [
        {
            'prompt': 'A cat playing in a garden',
            'model': 'RunwayML',
            'settings': {'duration': 5, 'resolution': '1280:720'}
        },
        {
            'prompt': 'A futuristic city at night',
            'model': 'ModelScope',
            'settings': {'duration': 10, 'resolution': '1920:1080'}
        },
        {
            'prompt': 'Ocean waves on a beach',
            'model': 'RunwayML',
            'settings': {'duration': 8, 'resolution': '1280:720'}
        }
    ]
    
    job_ids = processor.add_multiple_jobs(test_jobs)
    print(f"Added {len(job_ids)} jobs to the batch queue")
    
    # Monitor progress
    while processor.is_processing:
        status = processor.get_queue_status()
        print(f"Queue status: {status}")
        time.sleep(5)
    
    print("Batch processing completed!")
    
    # Export results
    results_file = processor.export_results()
    print(f"Results exported to: {results_file}")