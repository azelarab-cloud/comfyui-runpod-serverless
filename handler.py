import runpod
import subprocess
import requests
import time
import urllib.request
import json
import os
import base64

# Boot up the ComfyUI server in the background
def start_comfyui():
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

# Send the n8n workflow JSON to ComfyUI
def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

# Check if the image is done generating
def get_history(prompt_id):
    with urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}") as response:
        return json.loads(response.read())

# The main RunPod Serverless execution block
def handler(job):
    job_input = job['input']
    workflow = job_input.get('workflow') 
    
    if not workflow:
        return {"error": "No workflow provided by n8n."}

    # 1. Submit the job
    prompt_response = queue_prompt(workflow)
    prompt_id = prompt_response['prompt_id']
    
    # 2. Wait for completion
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            break
        time.sleep(1)
        
    # 3. Locate the generated image in the output folder
    output_dir = "./output"
    files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.png')]
    if not files:
         return {"error": "Generation failed. No image found."}
         
    latest_file = max(files, key=os.path.getctime)
    
    # 4. Convert the image to Base64 text to send back over HTTP
    with open(latest_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
    # Clean up the output folder so the serverless container doesn't get bloated
    os.remove(latest_file)
        
    return {"image_base64": encoded_string}

# Initialize server immediately when the container wakes up
start_comfyui()

# Start listening for n8n API calls
runpod.serverless.start({"handler": handler})
