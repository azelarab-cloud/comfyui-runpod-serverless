import runpod
import subprocess
import time

def handler(job):
    job_input = job['input']
    
    # 1. Start ComfyUI in the background
    # 2. Send the job_input (your n8n workflow JSON) to the ComfyUI API
    # 3. Wait for the image to generate in the output folder
    # 4. Read the image, convert to Base64
    
    return {"status": "success", "message": "ComfyUI generated the image"}

runpod.serverless.start({"handler": handler})
