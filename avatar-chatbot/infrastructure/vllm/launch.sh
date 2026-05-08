#!/bin/bash

MODEL=${VLLM_MODEL:-"mistralai/Mistral-7B-Instruct-v0.3"}
PORT=${VLLM_PORT:-8000}
QUANTIZATION=${VLLM_QUANTIZATION:-"awq"}

python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --port "$PORT" \
    --quantization "$QUANTIZATION" \
    --dtype auto \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.90 \
    --enable-prefix-caching \
    --enable-chunked-prefill \
    --max-num-seqs 256