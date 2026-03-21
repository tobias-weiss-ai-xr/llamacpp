# llama.cpp Server

Docker-based llama.cpp server for running quantized LLMs with NVIDIA GPU acceleration.

## Model

Currently configured for **Qwen3.5-35B-A3B** with Q4_K_M quantization (~20GB VRAM).

## Quick Start

```bash
# Start the server
docker compose up -d

# Check logs
docker compose logs -f

# Health check
curl http://localhost:8080/health
```

## API Usage

### Chat Completion (OpenAI-compatible)

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7
  }'
```

### Completion

```bash
curl http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a haiku about coding:",
    "n_predict": 50
  }'
```

### Metrics

```bash
curl http://localhost:8080/metrics
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL` | `/models/Qwen_Qwen3.5-35B-A3B-Q4_K_M.gguf` | Model path inside container |
| `MODELS_PATH` | `C:/Users/Tobias/.cache/llama.cpp/models` | Host models directory |
| `PORT` | `8080` | Host port |
| `CTX_SIZE` | `32768` | Context window size |
| `BATCH_SIZE` | `512` | Prompt processing batch size |
| `UBATCH_SIZE` | `128` | Micro-batch size for parallel decoding |
| `CACHE_TYPE` | `q8_0` | KV cache quantization (q8_0, f16, q4_0) |
| `N_PARALLEL` | `1` | Parallel decoding slots |

### VRAM Requirements

| Context | Q4_K_M | Q8_0 Cache |
|---------|--------|------------|
| 8K | ~18GB | ~20GB |
| 16K | ~20GB | ~22GB |
| 32K | ~22GB | ~26GB |

## Optimizations Applied

Based on [NVIDIA DGX Spark recommendations](https://forums.developer.nvidia.com/t/running-qwen-qwen3-5-35b-a3b-fp8-on-a-cluster/364168/5):

- **Flash Attention** (`-fa`): Faster attention computation
- **Continuous Batching** (`--cont-batching`): Better multi-request throughput
- **KV Cache Quantization** (`q8_0`): Reduces memory usage vs FP16
- **Full GPU Offload** (`-1` layers): All model layers on GPU
- **Metrics** (`--metrics`): Prometheus-compatible metrics endpoint

## Adding Models

1. Download GGUF model to your models directory
2. Set the `MODEL` environment variable:

```bash
MODEL=/models/your-model.gguf docker compose up -d
```

## Stopping

```bash
docker compose down
```
