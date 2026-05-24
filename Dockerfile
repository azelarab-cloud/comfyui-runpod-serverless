# Use a lightweight PyTorch base image
FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime

# Set working directory
WORKDIR /workspace

# Install git and clean up to save space
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git

# Set working directory to ComfyUI
WORKDIR /workspace/ComfyUI

# Install ComfyUI dependencies and RunPod
RUN pip install -r requirements.txt
RUN pip install runpod

# Copy your serverless handler script
COPY handler.py .

# Start the RunPod serverless worker
CMD ["python", "-u", "handler.py"]
