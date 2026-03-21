# Benchmark Results

## Current Setup (RTX 4080 Laptop - 12GB)

**Configuration:**
- Model: Qwen3.5-35B-A3B-Q4_K_M (19.76 GB, MoE with 256 experts)
- Context Window: 32,768 tokens
- GPU Layers: 15/40 offloaded
- KV Cache: q8_0 quantization
- GPU: NVIDIA RTX 4080 Laptop (12GB)
- GPU Memory: ~9.4GB used, ~2.6GB free

---

## Test Results

### Test 1: Short Prompt, Short Generation (20 tokens)

| Metric | Current (35B MoE) | Old Legion (9B) |
|--------|-------------------|-----------------|
| Total Time | 1,528ms | 2,009ms |
| Time to First Token | 413ms | 463ms |
| Generation Time | 989ms | 1,510ms |
| Tokens Generated | 20 | 20 |
| Tokens/sec | **20.22** | 13.2 |

**Result:** 53% faster generation than old setup

---

### Test 2: Long Prompt Processing (~1000 words, 20 tokens)

| Metric | Current (35B MoE) | Old Legion (9B) |
|--------|-------------------|-----------------|
| Total Time | 2,521ms | 2,426ms |
| Time to First Token | 1,439ms | 867ms |
| Generation Time | 950ms | 1,519ms |
| Prompt Tokens | 224 | 275 |
| Tokens/sec | **21.06** | 13.2 |

**Result:** 59% faster generation, 66% slower prompt processing (larger model)

---

### Test 3: Long Generation (200 tokens)

| Metric | Current (35B MoE) | Old Legion (9B) |
|--------|-------------------|-----------------|
| Total Time | 14,696ms | 16,191ms |
| Time to First Token | 460ms | 491ms |
| Generation Time | 13,508ms | 15,662ms |
| Tokens Generated | 200 | 200 |
| Tokens/sec | **14.81** | 12.77 |

**Result:** 16% faster generation

---

### Test 4: Concurrent Requests (5 Parallel, 50 tokens each)

| Metric | Current (35B MoE) | Old Legion (9B) |
|--------|-------------------|-----------------|
| Total Time | 10,935ms | 14,658ms |
| Avg per Request | 2,187ms | 2,931ms |
| Total Tokens | 250 | 250 |
| Throughput | **22.86 tokens/sec** | ~17 req/sec |
| Avg Tokens/sec | 11.19 | 5.5-13.0 |

**Result:** 25% faster concurrent processing

---

## GPU Memory Comparison

| Metric | Current (RTX 4080) | Old Legion (RTX 4090 6GB) |
|--------|-------------------|---------------------------|
| Total VRAM | 12,282 MB | 6,144 MB |
| Used | 9,431 MB (77%) | 4,688 MB (76%) |
| Free | 2,565 MB (21%) | 1,045 MB (17%) |
| Model Size | 19.76 GB | ~5.5 GB |

---

## Key Findings

### Strengths

1. **Faster Generation Speed**
   - Short gen: 20.22 vs 13.2 tokens/sec (+53%)
   - Long gen: 14.81 vs 12.77 tokens/sec (+16%)
   - Despite model being 4x larger (35B vs 9B)

2. **Better Concurrent Performance**
   - 25% faster total time for parallel requests
   - Higher throughput: 22.86 tokens/sec

3. **More Memory Headroom**
   - 21% free vs 17% free
   - Can potentially increase GPU layers

4. **MoE Efficiency**
   - 35B parameters, only ~3.5B active per token
   - Enables running larger model on same hardware

### Trade-offs

1. **Slower Long Prompt Processing**
   - TTFT for long prompts: 1,439ms vs 867ms (+66%)
   - Due to larger model size

2. **Higher Memory Usage**
   - 9.4GB vs 4.7GB used
   - But proportionally similar (77% vs 76%)

---

## Performance Summary

| Metric | Current | Old Legion | Change |
|--------|---------|------------|--------|
| Generation Speed (short) | 20.22 t/s | 13.2 t/s | **+53%** |
| Generation Speed (long) | 14.81 t/s | 12.77 t/s | **+16%** |
| TTFT (short prompt) | 413ms | 463ms | **-11%** |
| TTFT (long prompt) | 1,439ms | 867ms | +66% |
| Concurrent throughput | 22.86 t/s | ~17 t/s | **+34%** |
| Memory efficiency | 21% free | 17% free | **+24%** |

---

## Model Comparison

| Aspect | Qwen3.5-35B-A3B | Qwen3.5-9B |
|--------|-----------------|------------|
| Parameters | 35B (3.5B active MoE) | 9B dense |
| Experts | 256 experts, 8 active | N/A |
| Quantization | Q4_K_M (19.76 GB) | Q4_K_M (~5.5 GB) |
| Quality | Higher | Good |
| Speed (this hardware) | **Faster** | Slower |

---

## Recommendations

### Current Setup is Optimized For:
- Chat applications with long conversations
- Content generation
- Multi-user scenarios
- Quality-focused use cases

### To Improve TTFT for Long Prompts:
- Reduce context size (32K → 16K)
- Increase GPU layers (15 → 25) if memory allows
- Use smaller model variant if quality acceptable

### To Improve Throughput Further:
- Enable continuous batching (already supported)
- Increase parallel slots
- Consider multiple GPU setup

---

*Tested on: NVIDIA RTX 4080 Laptop (12GB), Windows, March 21, 2026*
