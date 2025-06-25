import torch
from diffusers import TextToVideoSDPipeline, DPMSolverMultistepScheduler
from diffusers.utils import export_to_video
import os # For output path manipulation

# Ensure FFmpeg is accessible for export_to_video, though it's often a system dependency.
# Users might need to install it separately: sudo apt-get install ffmpeg

def generate_video_modelscope(
    prompt: str,
    output_path: str,
    model_id: str = "damo-vilab/text-to-video-ms-1.7b",
    num_inference_steps: int = 25,
    guidance_scale: float = 9.0, # A common default, might need tuning
    num_frames: int = 25, # Default to a shorter video for quicker testing
    torch_dtype: torch.dtype = torch.float16, # Use float16 by default
    variant: str = "fp16", # Use fp16 variant by default
    seed: int | None = None
):
    """
    Generates a video using a ModelScopeT2V (or compatible) model from Hugging Face.

    Args:
        prompt (str): The text prompt to generate the video from.
        output_path (str): The full path to save the generated MP4 video.
        model_id (str): The Hugging Face model ID.
        num_inference_steps (int): Number of denoising steps.
        guidance_scale (float): Classifier-free guidance scale.
        num_frames (int): Number of frames to generate for the video.
        torch_dtype (torch.dtype): The torch dtype for model loading (e.g., torch.float16).
        variant (str): The model variant to load (e.g., "fp16").

    Returns:
        str: The path to the saved video file if successful.

    Raises:
        Exception: If any error occurs during model loading or video generation.
    """
    print(f"Initializing ModelScopeT2V video generation for prompt: \"{prompt}\"")
    print(f"Model ID: {model_id}, Output: {output_path}")
    print(f"Params: steps={num_inference_steps}, guidance={guidance_scale}, frames={num_frames}, seed={seed}")

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available. ModelScopeT2V requires a GPU.")

    try:
        # 1. Load the pipeline
        print(f"Loading model pipeline: {model_id} with dtype={torch_dtype}, variant={variant}...")
        pipe = TextToVideoSDPipeline.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            variant=variant
        )

        # 2. Set up the scheduler
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

        # 3. Move to GPU and enable memory optimizations
        print("Moving pipeline to GPU and enabling optimizations...")
        pipe.to("cuda")
        # Enable model CPU offload if GPU VRAM is limited.
        # This can slow down inference but helps fit larger models.
        # pipe.enable_model_cpu_offload() # Recommended for <16GB VRAM, but can be slow. Consider making this optional.

        # Enable VAE slicing for further memory saving on VAE decoding.
        pipe.enable_vae_slicing()

        # Set seed if provided
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cuda").manual_seed(seed)

        # 4. Generate video frames
        print(f"Generating video frames (num_frames={num_frames})...")
        # The pipeline call might have different or more specific arguments.
        # Based on typical diffusers pipelines:
        video_frames_output = pipe(
            prompt=prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            num_frames=num_frames,
            generator=generator # Pass the generator
            # width and height might be needed if not inferred from model config
            # For ModelScopeT2V, it's often 256x256 or similar fixed by the model.
            # Not explicitly setting width/height here, assuming model's default.
        )
        video_frames = video_frames_output.frames # This is a list of PIL.Image

        if not video_frames or len(video_frames) == 0:
            raise RuntimeError("Video generation resulted in no frames.")

        print(f"Successfully generated {len(video_frames)} frames.")

        # 5. Export frames to video
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print(f"Exporting frames to video at: {output_path}")
        # export_to_video can take an output_video_path argument.
        # It also takes an optional `fps` argument, defaulting to 10.
        export_to_video(video_frames, output_video_path=output_path, fps=10) # Defaulting to 10 FPS

        print(f"Video successfully saved to {output_path}")
        return output_path

    except Exception as e:
        print(f"Error during ModelScopeT2V video generation: {e}")
        # Re-raise the exception to be caught by the Gradio interface
        raise e

if __name__ == '__main__':
    # Example usage (requires a GPU and dependencies installed)
    # Ensure RUNWAY_API_KEY is not needed here, this is a local model test.
    if torch.cuda.is_available():
        print("Testing ModelScopeT2V generation...")
        test_prompt = "A panda surfing on a wave"
        test_output_dir = "test_opensource_videos"
        os.makedirs(test_output_dir, exist_ok=True)
        test_output_path = os.path.join(test_output_dir, "panda_surfing.mp4")

        try:
            # Using fewer frames for a quick test; default is 25 in the function
            # Using fewer inference steps for faster test, default is 25
            video_file = generate_video_modelscope(
                prompt=test_prompt,
                output_path=test_output_path,
                num_frames=16, # Shorter video for test
                num_inference_steps=20 # Fewer steps for test
            )
            print(f"Test video generated: {video_file}")
        except Exception as e:
            print(f"Test failed: {e}")
            print("Please ensure you have a CUDA-enabled GPU, sufficient VRAM, and all dependencies installed.")
            print("You might also need to log in to Hugging Face CLI: `huggingface-cli login` if the model requires it.")
    else:
        print("CUDA not available, skipping ModelScopeT2V test.")
