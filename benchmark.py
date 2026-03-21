#!/usr/bin/env python3
import requests
import time
import subprocess
import json

API_URL = "http://localhost:8080/v1/chat/completions"


def run_benchmark(name, messages, max_tokens):
    """Run a single benchmark test"""
    print(f"\n{name}")
    print("-" * 50)

    start = time.time()
    response = requests.post(
        API_URL, json={"model": "qwen", "messages": messages, "max_tokens": max_tokens}
    )
    elapsed = (time.time() - start) * 1000

    data = response.json()

    usage = data.get("usage", {})
    timings = data.get("timings", {})

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)

    prompt_ms = timings.get("prompt_ms", 0)
    predicted_ms = timings.get("predicted_ms", 0)
    tps = timings.get("predicted_per_second", 0)

    print(f"  Total time: {elapsed:.0f}ms")
    print(f"  Time to first token: {prompt_ms:.0f}ms")
    print(f"  Generation time: {predicted_ms:.0f}ms")
    print(f"  Prompt tokens: {prompt_tokens}")
    print(f"  Tokens generated: {completion_tokens}")
    print(f"  Total tokens: {total_tokens}")
    if tps > 0:
        print(f"  Tokens per second: {tps:.2f}")

    return {
        "total_ms": elapsed,
        "ttft_ms": prompt_ms,
        "gen_ms": predicted_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "tps": tps,
    }


def get_gpu_memory():
    """Get GPU memory stats"""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.total,memory.used,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
        )
        parts = result.stdout.strip().split(", ")
        return {
            "total_mb": int(parts[0]),
            "used_mb": int(parts[1]),
            "free_mb": int(parts[2]),
            "utilization_pct": int(parts[3]),
        }
    except:
        return None


def main():
    print("=" * 60)
    print("llama.cpp Benchmark - Qwen3.5-35B-A3B")
    print("=" * 60)

    gpu = get_gpu_memory()
    if gpu:
        print(f"\nGPU: RTX 4080 Laptop ({gpu['total_mb']} MB)")

    # Warmup
    print("\nWarmup request...")
    requests.post(
        API_URL,
        json={
            "model": "qwen",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
        },
    )

    results = {}

    # Test 1: Short prompt, short generation
    results["test1"] = run_benchmark(
        "Test 1: Short prompt, short generation (20 tokens)",
        [{"role": "user", "content": "Say hello"}],
        20,
    )

    # Test 2: Long prompt, short generation
    long_text = "The quick brown fox jumps over the lazy dog. " * 21
    results["test2"] = run_benchmark(
        "Test 2: Long prompt, short generation (~1000 words prompt, 20 tokens)",
        [{"role": "user", "content": f"Please summarize this: {long_text}"}],
        20,
    )

    # Test 3: Short prompt, long generation
    results["test3"] = run_benchmark(
        "Test 3: Short prompt, long generation (200 tokens)",
        [
            {
                "role": "user",
                "content": "Write a detailed explanation of quantum computing",
            }
        ],
        200,
    )

    # GPU Memory
    print("\n" + "=" * 60)
    print("GPU Memory After Tests")
    print("=" * 60)
    gpu = get_gpu_memory()
    if gpu:
        print(f"Total: {gpu['total_mb']} MB")
        print(f"Used: {gpu['used_mb']} MB")
        print(f"Free: {gpu['free_mb']} MB")
        print(f"Utilization: {gpu['utilization_pct']}%")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Test 1 (Short/Short): {results['test1']['total_ms']:.0f}ms total")
    print(
        f"Test 2 (Long/Short):  {results['test2']['total_ms']:.0f}ms total, {results['test2']['prompt_tokens']} prompt tokens"
    )
    print(
        f"Test 3 (Short/Long):  {results['test3']['total_ms']:.0f}ms total, {results['test3']['tps']:.2f} tokens/sec"
    )

    # Return results for documentation
    return results


if __name__ == "__main__":
    main()
