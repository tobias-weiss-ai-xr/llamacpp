#!/usr/bin/env python3
"""Compare context sizes for coding tasks"""

import subprocess
import requests
import time
import os

API_URL = "http://localhost:8080/v1/chat/completions"


def restart_with_context(ctx_size):
    """Restart container with new context size"""
    subprocess.run(["docker", "compose", "down"], capture_output=True)
    env = os.environ.copy()
    env["CTX_SIZE"] = str(ctx_size)
    subprocess.run(["docker", "compose", "up", "-d"], env=env, capture_output=True)

    # Wait for model to load
    for _ in range(60):  # Wait up to 2 minutes
        time.sleep(2)
        try:
            r = requests.get("http://localhost:8080/health", timeout=5)
            if r.json().get("status") == "ok":
                return True
        except:
            pass
    return False


def get_gpu_memory():
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
    )
    used, free = map(int, result.stdout.strip().split(", "))
    return used, free


def run_test(messages, max_tokens):
    """Run a single test and return metrics"""
    start = time.time()
    response = requests.post(
        API_URL,
        json={
            "model": "qwen",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        },
    )
    elapsed = (time.time() - start) * 1000

    data = response.json()
    usage = data.get("usage", {})
    timings = data.get("timings", {})

    return {
        "total_ms": elapsed,
        "ttft_ms": timings.get("prompt_ms", 0),
        "tps": timings.get("predicted_per_second", 0),
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
    }


def benchmark_coding(ctx_size):
    """Run coding benchmark for a specific context size"""

    # Test with medium code context
    code = """
class UserService:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_user(self, user_id: int) -> User:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, email: str, name: str) -> User:
        user = User(email=email, name=name)
        self.db.add(user)
        self.db.commit()
        return user
"""

    messages = [
        {
            "role": "user",
            "content": f"Add delete_user and list_users methods:\n```python\n{code}\n```",
        }
    ]

    # Warmup
    requests.post(
        API_URL,
        json={
            "model": "qwen",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
        },
    )

    # Run test 3 times and average
    results = []
    for _ in range(3):
        r = run_test(messages, 100)
        results.append(r)
        time.sleep(1)

    avg_tps = sum(r["tps"] for r in results) / len(results)
    avg_ttft = sum(r["ttft_ms"] for r in results) / len(results)

    used, free = get_gpu_memory()

    return {
        "ctx_size": ctx_size,
        "avg_tps": avg_tps,
        "avg_ttft": avg_ttft,
        "vram_used_mb": used,
        "vram_free_mb": free,
    }


def main():
    context_sizes = [32768, 49152, 65536]

    print("=" * 70)
    print("Context Size Optimization for Coding Tasks")
    print("=" * 70)

    results = []

    for ctx in context_sizes:
        print(f"\n>>> Testing {ctx // 1024}K context...")

        if not restart_with_context(ctx):
            print(f"  FAILED to load with {ctx} context")
            continue

        result = benchmark_coding(ctx)
        results.append(result)

        print(
            f"  VRAM: {result['vram_used_mb']}MB used, {result['vram_free_mb']}MB free"
        )
        print(f"  Speed: {result['avg_tps']:.2f} tokens/sec")
        print(f"  TTFT: {result['avg_ttft']:.0f}ms")

    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(
        f"{'Context':<12} {'VRAM Used':<12} {'VRAM Free':<12} {'Speed (t/s)':<14} {'TTFT (ms)':<12}"
    )
    print("-" * 70)

    for r in results:
        print(
            f"{r['ctx_size'] // 1024}K{'':<9} {r['vram_used_mb']}MB{'':<7} {r['vram_free_mb']}MB{'':<7} {r['avg_tps']:.2f}{'':<10} {r['avg_ttft']:.0f}"
        )

    # Find optimal
    best = max(results, key=lambda x: x["avg_tps"])
    print(f"\n>>> RECOMMENDED: {best['ctx_size'] // 1024}K context")
    print(
        f"    Best balance of speed ({best['avg_tps']:.2f} t/s) and memory ({best['vram_free_mb']}MB free)"
    )


if __name__ == "__main__":
    main()
