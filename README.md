# Polo Video Generation Scripts

This project contains Python scripts to interact with the RunwayML API for generating videos.

## Scripts

### 1. `runway_image_to_video.py`

Generates a video from an initial input image.

**Usage:**

```bash
python runway_image_to_video.py <input_image_path_or_uri> <output_video_path> [options]
```

**Examples:**

- Generate a video with default settings:
  ```bash
  python runway_image_to_video.py path/to/your/image.jpg generated_video.mp4
  ```

- Generate a 10-second video with a specific prompt and model:
  ```bash
  python runway_image_to_video.py https://example.com/image.png video_out.mp4 --duration 10 --text_prompt "camera pans left" --model_name gen4_turbo
  ```

Refer to the script's help message for more options:
```bash
python runway_image_to_video.py -h
```

### 2. `runway_text_to_video.py`

Generates a video from a text prompt. This script first generates an image based on the prompt and then uses that image to generate the video.

**Usage:**

```bash
python runway_text_to_video.py "<your_text_prompt>" <output_video_path> [options]
```

**Examples:**

- Generate a video from a text prompt with default settings:
  ```bash
  python runway_text_to_video.py "A futuristic cityscape" generated_video.mp4
  ```

- Generate a 10-second video with specific models and seed:
  ```bash
  python runway_text_to_video.py "A beautiful sunset over mountains" video_out.mp4 --duration 10 --i2v_model_name gen4_turbo --t2i_model_name gen4_image --seed 123
  ```

Refer to the script's help message for more options:
```bash
python runway_text_to_video.py -h
```

## Setup for both scripts

1.  **Install dependencies:**
    ```bash
    pip install runwayml requests
    ```

2.  **Set your RunwayML API Key:**
    You need to provide your RunwayML API key. This can be done in two ways:
    *   As an environment variable:
        ```bash
        export RUNWAY_API_KEY="your_api_key_here"
        ```
    *   Using the `--api_key` argument when running the script:
        ```bash
        python runway_text_to_video.py "My prompt" video.mp4 --api_key "your_api_key_here"
        ```

## Note on Models and Parameters

The available models, their parameters (like supported resolutions, duration limits), and pricing are subject to change by RunwayML. Please refer to the [official RunwayML API documentation](https://docs.dev.runwayml.com/) for the most up-to-date information.

---

## Web Interface (`app_gradio.py`)

A Gradio-based web interface is also provided for easy interaction with the text-to-video generation functionality.

### Running the Gradio App

1.  **Ensure Setup is Complete:**
    Follow the "Setup for scripts" section above. Make sure to install all dependencies from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    This file now includes dependencies for RunwayML, Gradio, and Hugging Face Diffusers (for ModelScopeT2V).

    Ensure your `RUNWAY_API_KEY` environment variable is set if you intend to use the RunwayML model.

2.  **Launch the App:**
    Navigate to the project directory in your terminal and run:
    ```bash
    python app_gradio.py
    ```

3.  **Open in Browser:**
    The script will output a local URL (usually `http://127.0.0.1:7860` or similar). Open this URL in your web browser to use the interface.

### Features

*   User-friendly interface for text prompt, duration, resolution, model selection, and seed.
*   Displays the generated video directly in the browser.
*   Provides real-time progress updates and error messages within the UI.
*   Output videos are saved in a `gradio_outputs` subdirectory within the project folder.

### Model Options in Gradio App

The Gradio app allows you to choose between different text-to-video models:

1.  **RunwayML:**
    *   Uses the RunwayML API for generation.
    *   Requires your `RUNWAY_API_KEY` environment variable to be set for this model to function.
    *   Generation happens on RunwayML's servers.
    *   Relevant parameters like resolution and specific RunwayML model names can be configured in the UI.

2.  **ModelScopeT2V (`damo-vilab/text-to-video-ms-1.7b`):**
    *   Uses the open-source ModelScope Text-to-Video model from Hugging Face.
    *   **Runs locally on your machine.**
    *   **Requires a CUDA-enabled GPU with sufficient VRAM (recommended 8GB+, ideally 12GB+ for typical use).** CPU-only execution is not supported by this script's integration.
    *   The first time you select this model for generation, the necessary model files (several GB) will be downloaded from Hugging Face. This may take a considerable amount of time depending on your internet connection. Subsequent runs will use the cached model (usually stored in `~/.cache/huggingface/hub/`).
    *   Video generation with ModelScopeT2V can be computationally intensive and time-consuming, especially for longer videos (more frames).
    *   **Dependencies:** Requires `torch`, `diffusers`, `transformers`, `accelerate`, and `einops`. These are included in `requirements.txt`. Ensure PyTorch is installed with CUDA support if you intend to use a GPU.
    *   **FFmpeg:** The `diffusers` library's video export utility (`export_to_video`) may require FFmpeg to be installed on your system and accessible in your system's PATH. If you encounter errors during video saving specifically for ModelScopeT2V, please ensure FFmpeg is installed. (e.g., on Debian/Ubuntu: `sudo apt update && sudo apt install ffmpeg`).

Please select the desired model from the dropdown in the UI. Note that some UI parameters are specific to RunwayML (like "RunwayML: Video Resolution", "RunwayML: Text-to-Image Model", "RunwayML: Image-to-Video Model") and will be ignored if ModelScopeT2V is selected. The "Video Duration (seconds) / Target Length" slider will influence the number of frames generated by ModelScopeT2V.