# llama.cpp Server

Docker-based llama.cpp server for running quantized LLMs with NVIDIA GPU acceleration.

## Model

Currently configured for **Qwen3.5-35B-A3B** with Q4_K_M quantization.

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
| `N_GPU_LAYERS` | `15` | GPU layers (adjust for your VRAM) |
| `CACHE_TYPE` | `q8_0` | KV cache quantization (f16, q8_0, q4_0) |

### GPU Layer Guidelines

| GPU VRAM | Recommended Layers |
|----------|-------------------|
| 8GB | 8-10 |
| 12GB | 15-20 |
| 16GB | 25-30 |
| 24GB | 35-40 (full offload) |

### Example: Custom Configuration

```bash
# Use a different model with larger context
MODEL=/models/Llama-3-70B-Q4_K_M.gguf \
CTX_SIZE=16384 \
N_GPU_LAYERS=30 \
docker compose up -d
```

## Optimizations

Based on [NVIDIA DGX Spark recommendations](https://forums.developer.nvidia.com/t/running-qwen-qwen3-5-35b-a3b-fp8-on-a-cluster/364168/5):

- **KV Cache Quantization** (`q8_0`): Reduces memory usage vs FP16 with minimal quality loss
- **Batch Processing** (`512`): Optimized prompt processing throughput
- **Metrics Endpoint** (`--metrics`): Prometheus-compatible monitoring

## Performance Notes

The Qwen3.5-35B-A3B is a Mixture-of-Experts (MoE) model with:
- 256 experts, 8 active per token
- ~35B total parameters, ~3.5B active per inference
- Enables efficient inference on consumer GPUs

## Adding Models

1. Download GGUF model to your models directory
2. Set the `MODEL` environment variable:

```bash
MODEL=/models/your-model.gguf docker compose up -d
```

## Troubleshooting

### Model loading stuck
- Pull the latest image: `docker pull ghcr.io/ggml-org/llama.cpp:server-cuda`
- Reduce `N_GPU_LAYERS` if you get OOM errors

### Slow inference
- Increase `N_GPU_LAYERS` to offload more to GPU
- Reduce `CTX_SIZE` if memory constrained

## Stopping

```bash
docker compose down
```
