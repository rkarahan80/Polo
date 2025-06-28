import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import pandas as pd

@dataclass
class GenerationEvent:
    """Data class for tracking video generation events."""
    id: str
    timestamp: datetime
    prompt: str
    model: str
    duration: float
    resolution: str
    status: str  # 'success', 'failed', 'cancelled'
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    user_rating: Optional[int] = None  # 1-5 stars
    tags: List[str] = None

class AnalyticsTracker:
    """
    Comprehensive analytics tracking system for video generation.
    Tracks usage patterns, performance metrics, and user behavior.
    """
    
    def __init__(self, db_path: str = "analytics.db"):
        """
        Initialize the analytics tracker.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create generations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generations (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                prompt TEXT NOT NULL,
                model TEXT NOT NULL,
                duration REAL NOT NULL,
                resolution TEXT NOT NULL,
                status TEXT NOT NULL,
                processing_time REAL,
                error_message TEXT,
                file_size INTEGER,
                user_rating INTEGER,
                tags TEXT
            )
        ''')
        
        # Create usage_stats table for daily/hourly aggregates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_stats (
                date TEXT NOT NULL,
                hour INTEGER NOT NULL,
                model TEXT NOT NULL,
                total_generations INTEGER DEFAULT 0,
                successful_generations INTEGER DEFAULT 0,
                failed_generations INTEGER DEFAULT 0,
                avg_processing_time REAL,
                total_duration REAL DEFAULT 0,
                PRIMARY KEY (date, hour, model)
            )
        ''')
        
        # Create user_sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT,
                total_generations INTEGER DEFAULT 0,
                session_duration REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def track_generation(self, event: GenerationEvent):
        """
        Track a video generation event.
        
        Args:
            event: GenerationEvent object with details
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert tags list to JSON string
        tags_json = json.dumps(event.tags) if event.tags else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO generations 
            (id, timestamp, prompt, model, duration, resolution, status, 
             processing_time, error_message, file_size, user_rating, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.id,
            event.timestamp.isoformat(),
            event.prompt,
            event.model,
            event.duration,
            event.resolution,
            event.status,
            event.processing_time,
            event.error_message,
            event.file_size,
            event.user_rating,
            tags_json
        ))
        
        # Update usage stats
        self._update_usage_stats(event)
        
        conn.commit()
        conn.close()
    
    def _update_usage_stats(self, event: GenerationEvent):
        """Update aggregated usage statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        date_str = event.timestamp.date().isoformat()
        hour = event.timestamp.hour
        
        # Get current stats
        cursor.execute('''
            SELECT total_generations, successful_generations, failed_generations,
                   avg_processing_time, total_duration
            FROM usage_stats 
            WHERE date = ? AND hour = ? AND model = ?
        ''', (date_str, hour, event.model))
        
        result = cursor.fetchone()
        
        if result:
            total_gen, success_gen, failed_gen, avg_time, total_dur = result
            
            # Update counts
            total_gen += 1
            if event.status == 'success':
                success_gen += 1
            elif event.status == 'failed':
                failed_gen += 1
            
            # Update processing time average
            if event.processing_time and avg_time:
                avg_time = (avg_time * (total_gen - 1) + event.processing_time) / total_gen
            elif event.processing_time:
                avg_time = event.processing_time
            
            # Update total duration
            total_dur += event.duration
            
            cursor.execute('''
                UPDATE usage_stats 
                SET total_generations = ?, successful_generations = ?, 
                    failed_generations = ?, avg_processing_time = ?, total_duration = ?
                WHERE date = ? AND hour = ? AND model = ?
            ''', (total_gen, success_gen, failed_gen, avg_time, total_dur, 
                  date_str, hour, event.model))
        else:
            # Insert new record
            success_gen = 1 if event.status == 'success' else 0
            failed_gen = 1 if event.status == 'failed' else 0
            
            cursor.execute('''
                INSERT INTO usage_stats 
                (date, hour, model, total_generations, successful_generations, 
                 failed_generations, avg_processing_time, total_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date_str, hour, event.model, 1, success_gen, failed_gen,
                  event.processing_time, event.duration))
        
        conn.commit()
        conn.close()
    
    def get_generation_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive generation statistics.
        
        Args:
            days: Number of days to look back
        
        Returns:
            Dictionary with various statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Total generations
        cursor.execute('''
            SELECT COUNT(*) FROM generations 
            WHERE timestamp >= ?
        ''', (start_date.isoformat(),))
        total_generations = cursor.fetchone()[0]
        
        # Success rate
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM generations 
            WHERE timestamp >= ?
        ''', (start_date.isoformat(),))
        
        success_data = cursor.fetchone()
        successful, failed, cancelled = success_data if success_data else (0, 0, 0)
        
        success_rate = (successful / total_generations * 100) if total_generations > 0 else 0
        
        # Average processing time
        cursor.execute('''
            SELECT AVG(processing_time) FROM generations 
            WHERE timestamp >= ? AND processing_time IS NOT NULL
        ''', (start_date.isoformat(),))
        avg_processing_time = cursor.fetchone()[0] or 0
        
        # Model usage
        cursor.execute('''
            SELECT model, COUNT(*) as count 
            FROM generations 
            WHERE timestamp >= ?
            GROUP BY model 
            ORDER BY count DESC
        ''', (start_date.isoformat(),))
        model_usage = dict(cursor.fetchall())
        
        # Popular resolutions
        cursor.execute('''
            SELECT resolution, COUNT(*) as count 
            FROM generations 
            WHERE timestamp >= ?
            GROUP BY resolution 
            ORDER BY count DESC
            LIMIT 5
        ''', (start_date.isoformat(),))
        popular_resolutions = dict(cursor.fetchall())
        
        # Average duration
        cursor.execute('''
            SELECT AVG(duration) FROM generations 
            WHERE timestamp >= ?
        ''', (start_date.isoformat(),))
        avg_duration = cursor.fetchone()[0] or 0
        
        # Daily generation counts
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count 
            FROM generations 
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp) 
            ORDER BY date
        ''', (start_date.isoformat(),))
        daily_counts = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_generations': total_generations,
            'successful_generations': successful,
            'failed_generations': failed,
            'cancelled_generations': cancelled,
            'success_rate': round(success_rate, 2),
            'avg_processing_time': round(avg_processing_time, 2),
            'avg_duration': round(avg_duration, 2),
            'model_usage': model_usage,
            'popular_resolutions': popular_resolutions,
            'daily_counts': daily_counts,
            'period_days': days
        }
    
    def get_hourly_usage_pattern(self, days: int = 7) -> Dict[int, int]:
        """
        Get hourly usage patterns.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary mapping hour (0-23) to generation count
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as count
            FROM generations 
            WHERE timestamp >= ?
            GROUP BY hour
            ORDER BY hour
        ''', (start_date.isoformat(),))
        
        hourly_data = dict(cursor.fetchall())
        conn.close()
        
        # Fill in missing hours with 0
        return {hour: hourly_data.get(hour, 0) for hour in range(24)}
    
    def get_model_performance(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance metrics for each model.
        
        Returns:
            Dictionary with model performance data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                model,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                AVG(CASE WHEN processing_time IS NOT NULL THEN processing_time END) as avg_time,
                AVG(duration) as avg_duration,
                AVG(CASE WHEN user_rating IS NOT NULL THEN user_rating END) as avg_rating
            FROM generations 
            GROUP BY model
        ''', )
        
        results = cursor.fetchall()
        conn.close()
        
        performance = {}
        for row in results:
            model, total, successful, avg_time, avg_duration, avg_rating = row
            success_rate = (successful / total * 100) if total > 0 else 0
            
            performance[model] = {
                'total_generations': total,
                'success_rate': round(success_rate, 2),
                'avg_processing_time': round(avg_time or 0, 2),
                'avg_duration': round(avg_duration or 0, 2),
                'avg_rating': round(avg_rating or 0, 2)
            }
        
        return performance
    
    def get_popular_prompts(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get most popular prompt patterns.
        
        Args:
            limit: Number of results to return
        
        Returns:
            List of (prompt_pattern, count) tuples
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all prompts
        cursor.execute('SELECT prompt FROM generations WHERE status = "success"')
        prompts = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Extract keywords and patterns
        word_counts = Counter()
        for prompt in prompts:
            # Simple word extraction (could be enhanced with NLP)
            words = prompt.lower().split()
            # Filter out common words
            filtered_words = [w for w in words if len(w) > 3 and w not in 
                            ['the', 'and', 'with', 'that', 'this', 'from', 'they', 'have']]
            word_counts.update(filtered_words)
        
        return word_counts.most_common(limit)
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """
        Analyze error patterns and common failure reasons.
        
        Returns:
            Dictionary with error analysis
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get error messages
        cursor.execute('''
            SELECT error_message, COUNT(*) as count 
            FROM generations 
            WHERE status = 'failed' AND error_message IS NOT NULL
            GROUP BY error_message 
            ORDER BY count DESC
        ''')
        error_patterns = dict(cursor.fetchall())
        
        # Get failure rate by model
        cursor.execute('''
            SELECT 
                model,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM generations 
            GROUP BY model
        ''')
        
        model_failure_rates = {}
        for model, total, failed in cursor.fetchall():
            failure_rate = (failed / total * 100) if total > 0 else 0
            model_failure_rates[model] = round(failure_rate, 2)
        
        # Get failure rate by time of day
        cursor.execute('''
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM generations 
            GROUP BY hour
        ''')
        
        hourly_failure_rates = {}
        for hour, total, failed in cursor.fetchall():
            failure_rate = (failed / total * 100) if total > 0 else 0
            hourly_failure_rates[hour] = round(failure_rate, 2)
        
        conn.close()
        
        return {
            'error_patterns': error_patterns,
            'model_failure_rates': model_failure_rates,
            'hourly_failure_rates': hourly_failure_rates
        }
    
    def generate_report(self, output_file: str = None, days: int = 30) -> str:
        """
        Generate a comprehensive analytics report.
        
        Args:
            output_file: Path to save the report (optional)
            days: Number of days to analyze
        
        Returns:
            Path to the generated report file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics_report_{timestamp}.json"
        
        # Gather all analytics data
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'period_days': days,
            'generation_stats': self.get_generation_stats(days),
            'hourly_usage': self.get_hourly_usage_pattern(days),
            'model_performance': self.get_model_performance(),
            'popular_prompts': self.get_popular_prompts(),
            'error_analysis': self.get_error_analysis()
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"Analytics report generated: {output_file}")
        return output_file
    
    def create_visualizations(self, output_dir: str = "analytics_charts"):
        """
        Create visualization charts for analytics data.
        
        Args:
            output_dir: Directory to save chart images
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # 1. Daily generation counts
        stats = self.get_generation_stats(30)
        daily_data = stats['daily_counts']
        
        if daily_data:
            plt.figure(figsize=(12, 6))
            dates = list(daily_data.keys())
            counts = list(daily_data.values())
            plt.plot(dates, counts, marker='o', linewidth=2, markersize=6)
            plt.title('Daily Video Generations (Last 30 Days)', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Number of Generations', fontsize=12)
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'daily_generations.png'), dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. Model usage pie chart
        model_data = stats['model_usage']
        if model_data:
            plt.figure(figsize=(10, 8))
            plt.pie(model_data.values(), labels=model_data.keys(), autopct='%1.1f%%', startangle=90)
            plt.title('Model Usage Distribution', fontsize=16, fontweight='bold')
            plt.axis('equal')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'model_usage.png'), dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Hourly usage pattern
        hourly_data = self.get_hourly_usage_pattern(7)
        plt.figure(figsize=(12, 6))
        hours = list(hourly_data.keys())
        counts = list(hourly_data.values())
        plt.bar(hours, counts, alpha=0.7, color='skyblue', edgecolor='navy')
        plt.title('Hourly Usage Pattern (Last 7 Days)', fontsize=16, fontweight='bold')
        plt.xlabel('Hour of Day', fontsize=12)
        plt.ylabel('Number of Generations', fontsize=12)
        plt.xticks(range(0, 24, 2))
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'hourly_usage.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Model performance comparison
        performance_data = self.get_model_performance()
        if performance_data:
            models = list(performance_data.keys())
            success_rates = [performance_data[model]['success_rate'] for model in models]
            avg_times = [performance_data[model]['avg_processing_time'] for model in models]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Success rates
            ax1.bar(models, success_rates, alpha=0.7, color='lightgreen', edgecolor='darkgreen')
            ax1.set_title('Success Rate by Model', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Success Rate (%)', fontsize=12)
            ax1.set_ylim(0, 100)
            
            # Processing times
            ax2.bar(models, avg_times, alpha=0.7, color='lightcoral', edgecolor='darkred')
            ax2.set_title('Average Processing Time by Model', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Processing Time (seconds)', fontsize=12)
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'model_performance.png'), dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"Visualization charts saved to {output_dir}")
    
    def export_data(self, output_file: str = None, format: str = 'csv') -> str:
        """
        Export raw analytics data.
        
        Args:
            output_file: Path to save the data (optional)
            format: Export format ('csv', 'json')
        
        Returns:
            Path to the exported file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics_data_{timestamp}.{format}"
        
        conn = sqlite3.connect(self.db_path)
        
        if format.lower() == 'csv':
            df = pd.read_sql_query('SELECT * FROM generations', conn)
            df.to_csv(output_file, index=False)
        elif format.lower() == 'json':
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM generations')
            columns = [description[0] for description in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        conn.close()
        print(f"Analytics data exported to {output_file}")
        return output_file

# Example usage and testing
if __name__ == "__main__":
    # Create analytics tracker
    tracker = AnalyticsTracker()
    
    # Add some sample data
    sample_events = [
        GenerationEvent(
            id="test_1",
            timestamp=datetime.now() - timedelta(hours=2),
            prompt="A cat playing in a garden",
            model="RunwayML",
            duration=5.0,
            resolution="1280:720",
            status="success",
            processing_time=45.2,
            file_size=1024000,
            user_rating=4,
            tags=["nature", "animals"]
        ),
        GenerationEvent(
            id="test_2",
            timestamp=datetime.now() - timedelta(hours=1),
            prompt="Futuristic city at night",
            model="ModelScope",
            duration=10.0,
            resolution="1920:1080",
            status="success",
            processing_time=78.5,
            file_size=2048000,
            user_rating=5,
            tags=["sci-fi", "urban"]
        )
    ]
    
    for event in sample_events:
        tracker.track_generation(event)
    
    # Generate reports
    stats = tracker.get_generation_stats(7)
    print("Generation Stats:", json.dumps(stats, indent=2))
    
    # Generate full report
    report_file = tracker.generate_report()
    print(f"Report generated: {report_file}")
    
    # Create visualizations
    tracker.create_visualizations()
    
    print("Analytics tracker test completed!")