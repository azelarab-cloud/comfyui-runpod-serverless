# Use a lightweight PyTorch base image
FROM pytorch/pytorch:2.5.0-cuda12.4-cudnn9-runtime

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git

# Set working directory to ComfyUI
WORKDIR /workspace/ComfyUI

# Install core dependencies, runpod, and the GGUF requirements
RUN pip install -r requirements.txt
RUN pip install runpod gguf protobuf

# Clone the custom GGUF node permanently into the image
RUN cd custom_nodes && git clone https://github.com/city96/ComfyUI-GGUF.git

# Copy your robust serverless handler script
COPY handler.py .

# Start the RunPod serverless worker
CMD ["python", "-u", "handler.py"]
