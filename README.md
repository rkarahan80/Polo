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
    Follow the "Setup for both scripts" section above. Make sure to install all dependencies from `requirements.txt`, which now includes `gradio`:
    ```bash
    pip install -r requirements.txt
    ```
    And ensure your `RUNWAY_API_KEY` environment variable is set.

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
*   Requires the `RUNWAY_API_KEY` environment variable to be set.
*   Output videos are saved in a `gradio_outputs` subdirectory within the project folder.