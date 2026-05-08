#!/bin/bash

echo "📥 Downloading AI models..."

MODELS_DIR="./ai-models"

# Create directories
mkdir -p "$MODELS_DIR/whisper"
mkdir -p "$MODELS_DIR/xtts"
mkdir -p "$MODELS_DIR/llm"

# Download Whisper model
echo "Downloading Whisper large-v3..."
# Models will be downloaded automatically by Faster-Whisper on first run

# Download XTTS-v2
echo "Downloading XTTS-v2..."
python3 -c "
from TTS.api import TTS
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2')
"

# Download embeddings model
echo "Downloading multilingual embeddings..."
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('intfloat/multilingual-e5-large')
"

echo "✅ All models downloaded!"