import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import os
import json
from typing import List, Tuple, Optional, Dict, Any
import subprocess
import tempfile

class VideoProcessor:
    """Advanced video processing utilities for AI-generated videos."""
    
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        self.temp_dir = tempfile.mkdtemp()
    
    def enhance_video_quality(self, input_path: str, output_path: str, 
                            enhancement_settings: Dict[str, Any] = None) -> bool:
        """
        Enhance video quality using various filters and adjustments.
        
        Args:
            input_path: Path to input video
            output_path: Path to save enhanced video
            enhancement_settings: Dictionary with enhancement parameters
        
        Returns:
            bool: Success status
        """
        if enhancement_settings is None:
            enhancement_settings = {
                'brightness': 1.1,
                'contrast': 1.2,
                'saturation': 1.1,
                'sharpness': 1.1,
                'denoise': True,
                'stabilize': False
            }
        
        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return False
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert to PIL for enhancement
                pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                
                # Apply enhancements
                if enhancement_settings.get('brightness', 1.0) != 1.0:
                    enhancer = ImageEnhance.Brightness(pil_image)
                    pil_image = enhancer.enhance(enhancement_settings['brightness'])
                
                if enhancement_settings.get('contrast', 1.0) != 1.0:
                    enhancer = ImageEnhance.Contrast(pil_image)
                    pil_image = enhancer.enhance(enhancement_settings['contrast'])
                
                if enhancement_settings.get('saturation', 1.0) != 1.0:
                    enhancer = ImageEnhance.Color(pil_image)
                    pil_image = enhancer.enhance(enhancement_settings['saturation'])
                
                if enhancement_settings.get('sharpness', 1.0) != 1.0:
                    enhancer = ImageEnhance.Sharpness(pil_image)
                    pil_image = enhancer.enhance(enhancement_settings['sharpness'])
                
                # Apply denoising
                if enhancement_settings.get('denoise', False):
                    pil_image = pil_image.filter(ImageFilter.MedianFilter(size=3))
                
                # Convert back to OpenCV format
                enhanced_frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                
                out.write(enhanced_frame)
                frame_count += 1
            
            cap.release()
            out.release()
            
            print(f"Enhanced video saved: {output_path} ({frame_count} frames processed)")
            return True
            
        except Exception as e:
            print(f"Error enhancing video: {e}")
            return False
    
    def create_video_montage(self, video_paths: List[str], output_path: str,
                           grid_size: Tuple[int, int] = (2, 2),
                           transition_duration: float = 0.5) -> bool:
        """
        Create a montage/grid of multiple videos.
        
        Args:
            video_paths: List of paths to input videos
            output_path: Path to save montage video
            grid_size: (rows, cols) for the grid layout
            transition_duration: Duration of transitions between videos
        
        Returns:
            bool: Success status
        """
        try:
            if len(video_paths) > grid_size[0] * grid_size[1]:
                print(f"Too many videos for grid size {grid_size}")
                return False
            
            # Open all video captures
            caps = []
            video_info = []
            
            for path in video_paths:
                cap = cv2.VideoCapture(path)
                if not cap.isOpened():
                    print(f"Could not open video: {path}")
                    continue
                
                caps.append(cap)
                video_info.append({
                    'fps': int(cap.get(cv2.CAP_PROP_FPS)),
                    'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                })
            
            if not caps:
                return False
            
            # Calculate output dimensions
            cell_width = 640  # Standard cell size
            cell_height = 360
            output_width = grid_size[1] * cell_width
            output_height = grid_size[0] * cell_height
            
            # Use the highest FPS
            output_fps = max(info['fps'] for info in video_info)
            
            # Setup output video
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, output_fps, (output_width, output_height))
            
            # Find the shortest video duration
            min_frames = min(info['frame_count'] for info in video_info)
            
            for frame_idx in range(min_frames):
                # Create the montage frame
                montage_frame = np.zeros((output_height, output_width, 3), dtype=np.uint8)
                
                for i, cap in enumerate(caps):
                    ret, frame = cap.read()
                    if not ret:
                        continue
                    
                    # Calculate grid position
                    row = i // grid_size[1]
                    col = i % grid_size[1]
                    
                    # Resize frame to cell size
                    resized_frame = cv2.resize(frame, (cell_width, cell_height))
                    
                    # Place in montage
                    y_start = row * cell_height
                    y_end = y_start + cell_height
                    x_start = col * cell_width
                    x_end = x_start + cell_width
                    
                    montage_frame[y_start:y_end, x_start:x_end] = resized_frame
                
                out.write(montage_frame)
            
            # Cleanup
            for cap in caps:
                cap.release()
            out.release()
            
            print(f"Video montage created: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error creating video montage: {e}")
            return False
    
    def add_text_overlay(self, input_path: str, output_path: str,
                        text: str, position: Tuple[int, int] = (50, 50),
                        font_scale: float = 1.0, color: Tuple[int, int, int] = (255, 255, 255),
                        duration: Optional[float] = None) -> bool:
        """
        Add text overlay to video.
        
        Args:
            input_path: Path to input video
            output_path: Path to save video with text overlay
            text: Text to overlay
            position: (x, y) position for text
            font_scale: Scale of the font
            color: RGB color of the text
            duration: Duration to show text (None for entire video)
        
        Returns:
            bool: Success status
        """
        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return False
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate frames to show text
            if duration:
                text_frames = int(duration * fps)
            else:
                text_frames = total_frames
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Add text overlay if within duration
                if frame_count < text_frames:
                    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                              font_scale, color, 2, cv2.LINE_AA)
                
                out.write(frame)
                frame_count += 1
            
            cap.release()
            out.release()
            
            print(f"Text overlay added: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error adding text overlay: {e}")
            return False
    
    def extract_frames(self, input_path: str, output_dir: str,
                      frame_interval: int = 30, max_frames: int = 100) -> List[str]:
        """
        Extract frames from video at specified intervals.
        
        Args:
            input_path: Path to input video
            output_dir: Directory to save extracted frames
            frame_interval: Extract every Nth frame
            max_frames: Maximum number of frames to extract
        
        Returns:
            List[str]: Paths to extracted frame images
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return []
            
            frame_paths = []
            frame_count = 0
            extracted_count = 0
            
            while extracted_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    frame_filename = f"frame_{extracted_count:04d}.jpg"
                    frame_path = os.path.join(output_dir, frame_filename)
                    
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)
                    extracted_count += 1
                
                frame_count += 1
            
            cap.release()
            print(f"Extracted {len(frame_paths)} frames to {output_dir}")
            return frame_paths
            
        except Exception as e:
            print(f"Error extracting frames: {e}")
            return []
    
    def create_timelapse(self, input_path: str, output_path: str,
                        speed_factor: float = 4.0) -> bool:
        """
        Create a timelapse version of the video.
        
        Args:
            input_path: Path to input video
            output_path: Path to save timelapse video
            speed_factor: How much to speed up the video
        
        Returns:
            bool: Success status
        """
        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return False
            
            # Get video properties
            original_fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate new FPS (keep reasonable limits)
            new_fps = min(original_fps * speed_factor, 60)
            frame_skip = int(speed_factor)
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, new_fps, (width, height))
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Skip frames based on speed factor
                if frame_count % frame_skip == 0:
                    out.write(frame)
                
                frame_count += 1
            
            cap.release()
            out.release()
            
            print(f"Timelapse created: {output_path} (speed: {speed_factor}x)")
            return True
            
        except Exception as e:
            print(f"Error creating timelapse: {e}")
            return False
    
    def add_background_music(self, video_path: str, audio_path: str,
                           output_path: str, audio_volume: float = 0.5) -> bool:
        """
        Add background music to video using FFmpeg.
        
        Args:
            video_path: Path to input video
            audio_path: Path to audio file
            output_path: Path to save video with audio
            audio_volume: Volume level for the audio (0.0 to 1.0)
        
        Returns:
            bool: Success status
        """
        try:
            # Use FFmpeg to combine video and audio
            cmd = [
                'ffmpeg', '-y',  # -y to overwrite output file
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',  # Copy video stream
                '-c:a', 'aac',   # Encode audio as AAC
                '-filter:a', f'volume={audio_volume}',
                '-shortest',     # End when shortest input ends
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Background music added: {output_path}")
                return True
            else:
                print(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error adding background music: {e}")
            return False
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a video file.
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dict with video information
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {}
            
            info = {
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                'codec': int(cap.get(cv2.CAP_PROP_FOURCC)),
                'file_size': os.path.getsize(video_path) if os.path.exists(video_path) else 0
            }
            
            cap.release()
            return info
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return {}
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during processing."""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print("Temporary files cleaned up")
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")

# Example usage and testing
if __name__ == "__main__":
    processor = VideoProcessor()
    
    # Example: Enhance a video
    # processor.enhance_video_quality(
    #     "input_video.mp4",
    #     "enhanced_video.mp4",
    #     {
    #         'brightness': 1.1,
    #         'contrast': 1.2,
    #         'saturation': 1.1,
    #         'denoise': True
    #     }
    # )
    
    print("Video processor initialized. Use the methods to process videos.")