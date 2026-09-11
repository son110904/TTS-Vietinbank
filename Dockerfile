FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers
ENV TORCH_HOME=/root/.cache/torch
ENV CUDA_VISIBLE_DEVICES=""

COPY app.py .
COPY ref_audio.wav .

RUN python - <<'PY'
from vieneu import Vieneu
print('Model cache ready')
PY

EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]