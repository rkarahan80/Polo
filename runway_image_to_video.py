import argparse
import os
import requests
from runwayml import RunwayML, TaskFailedError

def download_video(url, output_path):
    """Downloads a video from a URL to a local path."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad HTTP status codes
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Video downloaded successfully to {output_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading video (network/HTTP error): {e}")
        return False
    except IOError as e:
        print(f"Error writing video file to {output_path} (I/O error): {e}")
        return False
    return True

def main():
    epilog_text = """
Examples:
  # Generate a video with default settings:
  python runway_image_to_video.py path/to/your/image.jpg generated_video.mp4

  # Generate a 10-second video with a specific prompt and model:
  python runway_image_to_video.py https://example.com/image.png video_out.mp4 --duration 10 --text_prompt "camera pans left" --model_name gen4

Setup:
  1. Install the RunwayML SDK:
     pip install runwayml requests
  2. Set your RunwayML API key:
     - As an environment variable: export RUNWAY_API_KEY="your_api_key_here"
     - Or, pass it using the --api_key argument.
"""
    parser = argparse.ArgumentParser(
        description="Generate a video from an image using RunwayML API.",
        epilog=epilog_text,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input_image_path", help="Path or URI to the initial image.")
    parser.add_argument("output_video_path", help="Path to save the generated video.")
    parser.add_argument("--model_name", default="gen4_turbo", choices=["gen4_turbo", "gen4"],
                        help="RunwayML model to use (default: gen4_turbo).")
    parser.add_argument("--text_prompt", default="", help="Text prompt to describe the desired motion (optional).")
    parser.add_argument("--duration", type=int, default=5, choices=[5, 10],
                        help="Duration of the video in seconds (default: 5).")
    parser.add_argument("--resolution", default="1280:720",
                        help="Resolution of the video as 'width:height' (e.g., '1280:720', '720:1280'). Default: '1280:720'. See Gen-4 docs for supported resolutions.")
    parser.add_argument("--seed", type=int, help="Seed for fixed seed generation, for reproducible motion (optional).")
    parser.add_argument("--api_key", help="RunwayML API key. Can also be set via RUNWAY_API_KEY environment variable.")

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("RUNWAY_API_KEY")
    if not api_key:
        print("Error: RunwayML API key not found. Please provide it via --api_key or RUNWAY_API_KEY environment variable.")
        return

    try:
        client = RunwayML(api_key=api_key) # Explicitly pass api_key if SDK supports it, or it uses env var by default

        print(f"Initializing video generation with model: {args.model_name}...")
        task_params = {
            'model': args.model_name,
            'image_uri': args.input_image_path, # Assuming image_uri is the correct param name
            'duration': args.duration,
            'ratio': args.resolution, # Assuming ratio is the correct param name for resolution
        }
        if args.text_prompt:
            task_params['prompt_text'] = args.text_prompt
        if args.seed is not None:
            task_params['seed'] = args.seed # Assuming seed is the correct param for fixed_seed

        # Based on SDK structure: client.<task_type>.create(...)
        # The documentation suggests image_to_video is a valid task type.
        print("Sending request to RunwayML API...")
        task = client.image_to_video.create(**task_params).wait_for_task_output()

        if task.status == 'SUCCEEDED' and task.output and len(task.output) > 0:
            video_url = task.output[0] # Assuming the first output is the video URL
            print(f"Video generated successfully. URL: {video_url}")
            if not download_video(video_url, args.output_video_path):
                print("Failed to download the generated video.")
        else:
            print(f"Video generation failed or no output received. Status: {task.status}")
            if hasattr(task, 'error_message') and task.error_message:
                print(f"Error message: {task.error_message}")
            elif hasattr(task, 'task_details'):
                 print(f"Task details: {task.task_details}")


    except TaskFailedError as e:
        print(f"RunwayML task failed: {e}")
        if hasattr(e, 'task_details'):
            print(f"Task details: {e.task_details}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
