import argparse
import os
import requests # Added for video download
from runwayml import RunwayML, TaskFailedError

# Copied from runway_image_to_video.py
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
  # Generate a video from a text prompt with default settings:
  python runway_text_to_video.py "A futuristic cityscape" generated_video.mp4

  # Generate a 10-second video with a specific image-to-video model and text-to-image model:
  python runway_text_to_video.py "A beautiful sunset over mountains" video_out.mp4 --duration 10 --i2v_model_name gen4_turbo --t2i_model_name gen4_image --seed 123

Setup:
  1. Install the required libraries:
     pip install runwayml requests
  2. Set your RunwayML API key:
     - As an environment variable: export RUNWAY_API_KEY="your_api_key_here"
     - Or, pass it using the --api_key argument.
"""
    parser = argparse.ArgumentParser(
        description="Generate a video from a text prompt using RunwayML API by first generating an image and then converting it to video.",
        epilog=epilog_text,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("text_prompt", help="Text prompt to generate the initial image and guide video generation.")
    parser.add_argument("output_video_path", help="Path to save the generated video.")

    # Text-to-Image specific arguments
    parser.add_argument("--t2i_model_name", default="gen4_image",
                        help="RunwayML model to use for text-to-image generation (default: gen4_image).")
    # Consider adding arguments for image ratio/resolution for T2I if different from I2V

    # Image-to-Video specific arguments (similar to runway_image_to_video.py)
    parser.add_argument("--i2v_model_name", default="gen4_turbo", choices=["gen4_turbo", "gen3a_turbo"], # Updated based on docs
                        help="RunwayML model to use for image-to-video generation (default: gen4_turbo).")
    parser.add_argument("--duration", type=int, default=5, choices=[5, 10], # Based on Gen-4 Turbo outputs
                        help="Duration of the video in seconds (default: 5).")
    parser.add_argument("--resolution", default="1280:720",
                        help="Resolution of the video as 'width:height' (e.g., '1280:720'). Default: '1280:720'. See model docs for supported resolutions.")
    parser.add_argument("--seed", type=int, help="Seed for reproducible generation (optional). Applied to both T2I and I2V if not specified separately.")
    # It might be useful to have separate seeds: --t2i_seed and --i2v_seed

    parser.add_argument("--api_key", help="RunwayML API key. Can also be set via RUNWAY_API_KEY environment variable.")

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("RUNWAY_API_KEY")
    if not api_key:
        print("Error: RunwayML API key not found. Please provide it via --api_key or RUNWAY_API_KEY environment variable.")
        return

    print("Text-to-video script initialized with the following arguments:")
    print(f"  Text Prompt: {args.text_prompt}")
    print(f"  Output Video Path: {args.output_video_path}")
    print(f"  T2I Model: {args.t2i_model_name}")
    print(f"  I2V Model: {args.i2v_model_name}")
    print(f"  Duration: {args.duration}s")
    print(f"  Resolution: {args.resolution}")
    print(f"  Seed: {args.seed if args.seed is not None else 'Not set'}")

    try:
        client = RunwayML(api_key=api_key)

        # Step 1: Text-to-Image Generation
        print(f"\nInitiating text-to-image generation with model: {args.t2i_model_name}...")
        t2i_params = {
            'model': args.t2i_model_name,
            'prompt_text': args.text_prompt,
            # Assuming the image ratio for T2I should match the video resolution aspect ratio.
            # The API might expect 'width:height' or a predefined aspect ratio string.
            # For now, let's use the video resolution directly. This might need adjustment
            # based on what the text_to_image endpoint expects for 'ratio' or similar param.
            'ratio': args.resolution,
        }
        if args.seed is not None:
            t2i_params['seed'] = args.seed

        print("Sending request to RunwayML API for text-to-image...")
        t2i_task = client.text_to_image.create(**t2i_params).wait_for_task_output()

        if t2i_task.status == 'SUCCEEDED' and t2i_task.output and len(t2i_task.output) > 0:
            generated_image_uri = t2i_task.output[0] # Assuming the first output is the image URI
            print(f"Image generated successfully. URI: {generated_image_uri}")

            # Step 2: Image-to-Video Generation
            print(f"\nInitiating image-to-video generation with model: {args.i2v_model_name}...")
            i2v_params = {
                'model': args.i2v_model_name,
                'image_uri': generated_image_uri,
                'duration': args.duration,
                'ratio': args.resolution, # This is 'ratio' for I2V as per existing script
                'prompt_text': args.text_prompt, # Pass the original prompt to guide video motion
            }
            if args.seed is not None:
                i2v_params['seed'] = args.seed # Use the same seed for I2V

            print("Sending request to RunwayML API for image-to-video...")
            i2v_task = client.image_to_video.create(**i2v_params).wait_for_task_output()

            if i2v_task.status == 'SUCCEEDED' and i2v_task.output and len(i2v_task.output) > 0:
                generated_video_url = i2v_task.output[0] # Assuming the first output is the video URL
                print(f"Video generated successfully. URL: {generated_video_url}")

                # Step 3: Download Video
                if not download_video(generated_video_url, args.output_video_path):
                    print("Failed to download the generated video.")
                # If download fails, the script will continue and exit normally after this.
                # Consider if an explicit exit/error is needed if download is critical.
            else:
                print(f"Image-to-video generation failed or no output received. Status: {i2v_task.status}")
                if hasattr(i2v_task, 'error_message') and i2v_task.error_message:
                    print(f"Error message: {i2v_task.error_message}")
                elif hasattr(i2v_task, 'task_details'):
                    print(f"Task details: {i2v_task.task_details}")
                return # Exit if video generation failed
        else:
            print(f"Text-to-image generation failed or no output received. Status: {t2i_task.status}")
            if hasattr(t2i_task, 'error_message') and t2i_task.error_message:
                print(f"Error message: {t2i_task.error_message}")
            elif hasattr(t2i_task, 'task_details'):
                 print(f"Task details: {t2i_task.task_details}")
            return # Exit if image generation failed

    except TaskFailedError as e:
        print(f"RunwayML text-to-image task failed: {e}")
        if hasattr(e, 'task_details'):
            print(f"Task details: {e.task_details}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
