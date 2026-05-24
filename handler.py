import runpod
import subprocess
import time
import requests
import json
import urllib.request
import os
import base64

def start_comfyui():
    print("Configuring ComfyUI to read from the Network Volume...")
    
    # This tells ComfyUI exactly where your comfy_persist files are hiding on the RunPod volume
    yaml_content = """
runpod_volume:
    base_path: /runpod-volume/comfy_persist/models
    checkpoints: checkpoints
    clip: text_encoders
    text_encoders: text_encoders
    unet: diffusion_models
    diffusion_models: diffusion_models
    vae: vae
    loras: loras
"""
    with open("extra_model_paths.yaml", "w") as f:
        f.write(yaml_content)
        
    print("Starting ComfyUI Engine...")
    subprocess.Popen(["python", "main.py", "--listen", "127.0.0.1", "--port", "8188"])
    
    # Poll until the server is ready to accept API calls
    while True:
        try:
            response = requests.get("http://127.0.0.1:8188/")
            if response.status_code == 200:
                print("ComfyUI is ready!")
                break
        except requests.exceptions.ConnectionError:
            time.sleep(1)

def queue_prompt(prompt_workflow):
    """Sends the workflow to ComfyUI for generation."""
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    req.add_header('Content-Type', 'application/json')
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

def get_history(prompt_id):
    """Checks the status of the job inside ComfyUI."""
    with urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}") as response:
        return json.loads(response.read())

def handler(job):
    """The main RunPod serverless handler."""
    workflow = job['input']['workflow']
    
    print("Received job, queuing prompt...")
    prompt_response = queue_prompt(workflow)
    prompt_id = prompt_response['prompt_id']
    
    print(f"Prompt queued. ID: {prompt_id}")
    
    # Poll ComfyUI until the image generation is complete
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            print("Generation complete!")
            
            # Extract the generated image filenames
            outputs = history[prompt_id]['outputs']
            images = []
            
            for node_id in outputs:
                if 'images' in outputs[node_id]:
                    for image in outputs[node_id]['images']:
                        # ComfyUI typically saves outputs to the /workspace/ComfyUI/output folder
                        image_path = os.path.join("output", image['filename'])
                        
                        # Convert the image to base64 so it can be sent back to your local computer
                        with open(image_path, "rb") as img_file:
                            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                            images.append({
                                "filename": image['filename'],
                                "image_base64": encoded_string
                            })
            
            return {"status": "success", "images": images}
        
        # Wait 2 seconds before checking again
        time.sleep(2)

# 1. Start the ComfyUI engine in the background
start_comfyui()

# 2. Start the RunPod worker and wait for API requests
print("Starting RunPod Serverless Worker...")
runpod.serverless.start({"handler": handler})
