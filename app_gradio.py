import gradio as gr
import os
import requests # For download_video
from runwayml import RunwayML, TaskFailedError

# Copied and adapted from runway_image_to_video.py for use here
def download_video(url, output_path):
    """Downloads a video from a URL to a local path."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Video downloaded successfully to {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading video (network/HTTP error): {e}")
        # For Gradio, it's better to raise an error that can be displayed
        raise gr.Error(f"Error downloading video (network/HTTP error): {e}")
    except IOError as e:
        print(f"Error writing video file to {output_path} (I/O error): {e}")
        raise gr.Error(f"Error writing video file to {output_path} (I/O error): {e}")

# Core logic adapted from runway_text_to_video.py
def generate_video_from_text_internal(api_key, text_prompt, output_video_path, t2i_model_name, i2v_model_name, duration, resolution, seed):
    print(f"Initiating video generation for prompt: '{text_prompt}'")
    client = RunwayML(api_key=api_key)

    # Step 1: Text-to-Image Generation
    print(f"Step 1: Text-to-Image with model {t2i_model_name}")
    gr.Info("Generating initial image...") # Gradio feedback
    t2i_params = {
        'model': t2i_model_name,
        'prompt_text': text_prompt,
        'ratio': resolution, # Assuming T2I also uses 'width:height' for ratio
    }
    if seed is not None:
        t2i_params['seed'] = seed

    try:
        t2i_task = client.text_to_image.create(**t2i_params).wait_for_task_output()
    except TaskFailedError as e:
        print(f"RunwayML text-to-image task failed: {e}")
        raise gr.Error(f"Text-to-image task failed: {e.task_details if hasattr(e, 'task_details') else str(e)}")
    except Exception as e:
        print(f"Error during text-to-image: {e}")
        raise gr.Error(f"Error during text-to-image: {str(e)}")

    if not (t2i_task.status == 'SUCCEEDED' and t2i_task.output and len(t2i_task.output) > 0):
        error_msg = f"Text-to-image generation failed. Status: {t2i_task.status}."
        if hasattr(t2i_task, 'error_message') and t2i_task.error_message:
            error_msg += f" Message: {t2i_task.error_message}"
        elif hasattr(t2i_task, 'task_details'):
            error_msg += f" Details: {t2i_task.task_details}"
        print(error_msg)
        raise gr.Error(error_msg)

    generated_image_uri = t2i_task.output[0]
    print(f"Image generated successfully. URI: {generated_image_uri}")

    # Step 2: Image-to-Video Generation
    print(f"Step 2: Image-to-Video with model {i2v_model_name}")
    gr.Info("Generating video from image...") # Gradio feedback
    i2v_params = {
        'model': i2v_model_name,
        'image_uri': generated_image_uri,
        'duration': duration,
        'ratio': resolution,
        'prompt_text': text_prompt, # Guiding video motion
    }
    if seed is not None:
        i2v_params['seed'] = seed

    try:
        i2v_task = client.image_to_video.create(**i2v_params).wait_for_task_output()
    except TaskFailedError as e:
        print(f"RunwayML image-to-video task failed: {e}")
        raise gr.Error(f"Image-to-video task failed: {e.task_details if hasattr(e, 'task_details') else str(e)}")
    except Exception as e:
        print(f"Error during image-to-video: {e}")
        raise gr.Error(f"Error during image-to-video: {str(e)}")

    if not (i2v_task.status == 'SUCCEEDED' and i2v_task.output and len(i2v_task.output) > 0):
        error_msg = f"Image-to-video generation failed. Status: {i2v_task.status}."
        if hasattr(i2v_task, 'error_message') and i2v_task.error_message:
            error_msg += f" Message: {i2v_task.error_message}"
        elif hasattr(i2v_task, 'task_details'):
            error_msg += f" Details: {i2v_task.task_details}"
        print(error_msg)
        raise gr.Error(error_msg)

    generated_video_url = i2v_task.output[0]
    print(f"Video generated successfully. URL: {generated_video_url}")

    # Step 3: Download Video
    print("Step 3: Downloading video...")
    gr.Info("Downloading generated video...") # Gradio feedback
    if download_video(generated_video_url, output_video_path):
        print(f"Video downloaded to {output_video_path}")
        return output_video_path
    else:
        # download_video now raises gr.Error, so this path might not be hit if it's an error.
        # However, if it returned False for some other reason:
        raise gr.Error("Failed to download the generated video after successful generation.")


# Gradio interface function
def gradio_interface(prompt, duration_sec, resolution_str, t2i_model, i2v_model, seed_val):
    print(f"Gradio interface called with prompt: {prompt}")
    api_key = os.environ.get("RUNWAY_API_KEY")
    if not api_key:
        # Gradio provides gr.Error to show errors in the UI
        raise gr.Error("RUNWAY_API_KEY environment variable not set.")

    # Define a unique output path for each generation, perhaps in a temporary directory
    # For simplicity, placing it in the current directory with a timestamp or random name.
    # Gradio handles temporary files well if the output component expects a filepath.
    # Let's create a directory for outputs if it doesn't exist.
    os.makedirs("gradio_outputs", exist_ok=True)
    output_filename = f"gradio_outputs/video_{abs(hash(prompt + str(seed_val)))}.mp4" # Simple unique name

    try:
        # Convert seed_val to int, None if 0 or empty
        processed_seed = int(seed_val) if seed_val and int(seed_val) != 0 else None

        # Call the internal function that encapsulates the logic from runway_text_to_video.py
        video_path = generate_video_from_text_internal(
            api_key,
            prompt,
            output_filename,
            t2i_model,
            i2v_model,
            duration_sec,
            resolution_str,
            processed_seed
        )
        return video_path
    except TaskFailedError as e:
        print(f"RunwayML Task Failed: {e}")
        raise gr.Error(f"RunwayML Task Failed: {e.task_details if hasattr(e, 'task_details') else str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Show a generic error in the Gradio interface
        raise gr.Error(f"An unexpected error occurred: {str(e)}")

# Define Gradio components
prompt_input = gr.Textbox(label="Text Prompt", placeholder="e.g., A futuristic cityscape")
duration_input = gr.Slider(minimum=1, maximum=15, value=5, step=1, label="Video Duration (seconds)") # Max duration might depend on model
resolution_choices = ["1280:720", "720:1280", "1024:1024", "1920:1080"] # Common resolutions
resolution_input = gr.Dropdown(choices=resolution_choices, value="1280:720", label="Video Resolution (Width:Height)")

# Based on runway_text_to_video.py and docs
t2i_model_choices = ["gen4_image"] # Currently only one shown in docs, but could expand
t2i_model_input = gr.Dropdown(choices=t2i_model_choices, value="gen4_image", label="Text-to-Image Model")

i2v_model_choices = ["gen4_turbo", "gen3a_turbo"]
i2v_model_input = gr.Dropdown(choices=i2v_model_choices, value="gen4_turbo", label="Image-to-Video Model")

seed_input = gr.Number(label="Seed (0 or empty for random)", value=0)

video_output = gr.Video(label="Generated Video")

# Create the Gradio interface
iface = gr.Interface(
    fn=gradio_interface,
    inputs=[prompt_input, duration_input, resolution_input, t2i_model_input, i2v_model_input, seed_input],
    outputs=video_output,
    title="Text-to-Video Generator using RunwayML",
    description="Enter a text prompt and parameters to generate a video. Requires RUNWAY_API_KEY environment variable.",
    allow_flagging="never"
)

if __name__ == "__main__":
    print("Launching Gradio interface...")
    # Make sure RUNWAY_API_KEY is set in your environment before running.
    if not os.environ.get("RUNWAY_API_KEY"):
        print("Warning: RUNWAY_API_KEY is not set. The app will load but generation will fail.")
    iface.launch()
